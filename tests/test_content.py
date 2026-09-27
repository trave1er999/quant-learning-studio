"""Learning-content catalog and validation tests.

Authored content is project-original; tests check structure, versioning, source
binding and that the public view never leaks the quiz answers.
"""
import json
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app import content as content_mod


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(content_mod.router)
    with TestClient(app) as test_client:
        yield test_client


def valid_lesson(lesson_id='lesson-test'):
    return {'id': lesson_id, 'title': '测试课程', 'minutes': 3, 'tag': '测试', 'body': '正文', 'question': '问题？',
            'options': ['A', 'B', 'C'], 'answer': 0, 'explanation': '解释'}


def valid_term(term='测试术语'):
    return {'term': term, 'definition': '定义'}


def test_catalog_loads_backward_compatible_names():
    assert len(content_mod.LESSONS) >= 5
    assert len(content_mod.GLOSSARY) >= 6
    assert all(set(['id', 'title', 'minutes', 'tag', 'body', 'question', 'options', 'answer', 'explanation']) <= set(lesson) for lesson in content_mod.LESSONS)


def test_public_lessons_hide_answers():
    for lesson in content_mod.list_lessons():
        assert 'answer' not in lesson and 'explanation' not in lesson
    detail = content_mod.get_lesson('risk')
    assert 'answer' not in detail
    assert content_mod.get_lesson('risk', include_answer=True)['answer'] == 1


def test_unknown_lesson_raises():
    with pytest.raises(content_mod.ContentError):
        content_mod.get_lesson('nope')


def test_list_lessons_filter_by_tag_and_query():
    assert all(row['tag'] == '先看风险' for row in content_mod.list_lessons(tag='先看风险'))
    assert content_mod.list_lessons(q='最大回撤')
    assert content_mod.list_lessons(q='不存在的词') == []


def test_glossary_entries_carry_version_and_source():
    terms = content_mod.list_glossary()
    assert terms and all(t['version'] and t['source_id'] and t['review_status'] == 'REVIEWED' for t in terms)
    assert content_mod.list_glossary(q='回撤')
    assert content_mod.lookup_terms('什么是最大回撤？') == ['最大回撤']


def test_content_metadata_reports_scope_and_counts():
    meta = content_mod.content_metadata()
    assert meta['lessons']['scope'] == 'LESSON' and meta['lessons']['count'] == len(content_mod.LESSONS)
    assert meta['glossary']['scope'] == 'GLOSSARY' and meta['glossary']['review_status'] == 'REVIEWED'


def test_validate_lesson_rejects_bad_entries():
    for bad in ({**valid_lesson(), 'answer': 9}, {**valid_lesson(), 'options': ['only']},
                {**valid_lesson(), 'minutes': 0}, {k: v for k, v in valid_lesson().items() if k != 'body'}):
        with pytest.raises(content_mod.ContentError):
            content_mod.validate_lesson(bad)


def test_validate_lesson_duplicate_id():
    seen = set()
    content_mod.validate_lesson(valid_lesson(), seen)
    with pytest.raises(content_mod.ContentError) as exc:
        content_mod.validate_lesson(valid_lesson(), seen)
    assert any('重复' in reason for reason in exc.value.reasons)


def test_validate_glossary_rejects_bad_entries():
    for bad in ({'term': 'x'}, {'definition': 'y'}, {'term': '', 'definition': 'z'}):
        with pytest.raises(content_mod.ContentError):
            content_mod.validate_glossary_term(bad)
    seen = set()
    content_mod.validate_glossary_term(valid_term(), seen)
    with pytest.raises(content_mod.ContentError):
        content_mod.validate_glossary_term(valid_term(), seen)


def test_validate_catalog_rejects_invalid_documents():
    lessons = {'catalog_version': '1.0.0', 'scope': 'LESSON', 'source_id': 's', 'review_status': 'REVIEWED', 'lessons': [valid_lesson()]}
    glossary = {'catalog_version': '1.0.0', 'scope': 'GLOSSARY', 'source_id': 's', 'review_status': 'REVIEWED', 'terms': [valid_term()]}
    assert content_mod.validate_catalog(lessons, glossary) is True
    for broken in (dict(lessons, scope='WRONG'), dict(lessons, lessons=[]), dict(lessons, review_status='NOPE'), dict(lessons, source_id=None)):
        with pytest.raises(content_mod.ContentError):
            content_mod.validate_catalog(broken, glossary)


def test_load_content_rejects_bad_temp_dir(tmp_path):
    (tmp_path / 'lessons').mkdir(parents=True)
    (tmp_path / 'glossary').mkdir(parents=True)
    (tmp_path / 'lessons' / 'lessons.json').write_text(json.dumps({'catalog_version': '1.0.0', 'scope': 'LESSON', 'source_id': 's', 'review_status': 'REVIEWED', 'lessons': []}), encoding='utf-8')
    (tmp_path / 'glossary' / 'glossary.json').write_text(json.dumps({'catalog_version': '1.0.0', 'scope': 'GLOSSARY', 'source_id': 's', 'review_status': 'REVIEWED', 'terms': [valid_term()]}), encoding='utf-8')
    with pytest.raises(content_mod.ContentError):
        content_mod.load_content(tmp_path)


def test_missing_content_file_raises(tmp_path):
    with pytest.raises(content_mod.ContentError):
        content_mod.load_content(tmp_path)


def test_require_reviewed_blocks_unreviewed_doc():
    assert content_mod.require_reviewed({'review_status': 'REVIEWED'}, '课程') is True
    with pytest.raises(content_mod.ContentError):
        content_mod.require_reviewed({'review_status': 'UNREVIEWED'}, '课程')


def test_http_lessons_and_glossary(client):
    lessons = client.get('/api/catalog/lessons').json()
    assert lessons['lessons'] and all('answer' not in row for row in lessons['lessons'])
    assert lessons['version'] and lessons['source_id']
    assert client.get('/api/catalog/lessons/risk').json()['lesson']['id'] == 'risk'
    assert client.get('/api/catalog/lessons/nope').status_code == 404
    glossary = client.get('/api/catalog/glossary').json()
    assert glossary['terms'] and glossary['terms'][0]['term']
    assert client.get('/api/catalog/metadata').status_code == 200


def test_http_validate_content(client):
    assert client.post('/api/catalog/validate', json={'kind': 'lesson', 'payload': valid_lesson()}).json()['valid'] is True
    bad = client.post('/api/catalog/validate', json={'kind': 'lesson', 'payload': {'id': 'x'}}).json()
    assert bad['valid'] is False and bad['reasons']
    assert client.post('/api/catalog/validate', json={'kind': 'unknown', 'payload': {}}).json()['valid'] is False

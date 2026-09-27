"""Authored learning content catalog; never presented as real fund records.

Content is authored in-repo and loaded from content/lessons and content/glossary.
Loading is fail-closed: invalid or missing content raises ContentError instead of
silently serving unverified material. LESSONS and GLOSSARY remain available for
backward compatibility with app.main.
"""
from __future__ import annotations
import json, os
from pathlib import Path
from fastapi import APIRouter, HTTPException

VERSION = 'qlab-content-catalog-1.0.0'
ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONTENT_DIR = Path(os.environ.get('QLAB_CONTENT_DIR', str(ROOT / 'content')))

LESSON_REQUIRED = ['id', 'title', 'minutes', 'tag', 'body', 'question', 'options', 'answer', 'explanation']
GLOSSARY_REQUIRED = ['term', 'definition']
REVIEW_STATUSES = {'REVIEWED', 'UNREVIEWED', 'REJECTED'}
PUBLIC_LESSON_EXCLUDE = {'answer', 'explanation'}


class ContentError(ValueError):
    def __init__(self, message, reasons=None):
        reasons = list(reasons) if reasons else [message]
        super().__init__(message)
        self.reasons = reasons


def _read_json(path):
    path = Path(path)
    try:
        with open(path, encoding='utf-8') as handle:
            data = json.load(handle)
    except FileNotFoundError:
        raise ContentError(f'缺少内容文件：{path.name}', [f'缺少内容文件：{path}'])
    except json.JSONDecodeError as exc:
        raise ContentError(f'内容文件不是合法 JSON：{path.name}', [f'内容文件不是合法 JSON：{path}（{exc.msg}）'])
    if not isinstance(data, dict):
        raise ContentError(f'内容文件根节点必须是对象：{path.name}', [f'内容文件根节点必须是对象：{path}'])
    return data


def _require_str(value, field, errors):
    if not isinstance(value, str) or not value.strip():
        errors.append(f'字段 {field} 必须是非空字符串')


def validate_lesson(lesson, seen_ids=None):
    errors = []
    if not isinstance(lesson, dict):
        raise ContentError('课程条目必须是对象', ['课程条目必须是对象'])
    for field in LESSON_REQUIRED:
        if field not in lesson:
            errors.append(f'课程缺少必填字段 {field}')
    _require_str(lesson.get('id'), 'id', errors)
    _require_str(lesson.get('title'), 'title', errors)
    _require_str(lesson.get('tag'), 'tag', errors)
    _require_str(lesson.get('body'), 'body', errors)
    _require_str(lesson.get('question'), 'question', errors)
    _require_str(lesson.get('explanation'), 'explanation', errors)
    minutes = lesson.get('minutes')
    if not isinstance(minutes, int) or isinstance(minutes, bool) or minutes <= 0:
        errors.append('字段 minutes 必须是正整数')
    options = lesson.get('options')
    if not isinstance(options, list) or len(options) < 2 or any(not isinstance(o, str) or not o.strip() for o in options):
        errors.append('字段 options 必须是至少两项的非空字符串列表')
    answer = lesson.get('answer')
    if not isinstance(answer, int) or isinstance(answer, bool):
        errors.append('字段 answer 必须是整数索引')
    elif isinstance(options, list) and not 0 <= answer < len(options):
        errors.append('字段 answer 超出 options 范围')
    lesson_id = lesson.get('id')
    if seen_ids is not None and isinstance(lesson_id, str) and lesson_id.strip():
        if lesson_id in seen_ids:
            errors.append(f'课程 id 重复：{lesson_id}')
        seen_ids.add(lesson_id)
    if errors:
        raise ContentError('课程内容校验失败', errors)
    return True


def validate_glossary_term(entry, seen_terms=None):
    errors = []
    if not isinstance(entry, dict):
        raise ContentError('术语条目必须是对象', ['术语条目必须是对象'])
    for field in GLOSSARY_REQUIRED:
        if field not in entry:
            errors.append(f'术语缺少必填字段 {field}')
    _require_str(entry.get('term'), 'term', errors)
    _require_str(entry.get('definition'), 'definition', errors)
    term = entry.get('term')
    if seen_terms is not None and isinstance(term, str) and term.strip():
        if term in seen_terms:
            errors.append(f'术语重复：{term}')
        seen_terms.add(term)
    if errors:
        raise ContentError('术语内容校验失败', errors)
    return True


def validate_catalog(lessons_doc, glossary_doc):
    errors = []
    for key, doc, label, scope in [('lessons', lessons_doc, '课程', 'LESSON'), ('terms', glossary_doc, '术语', 'GLOSSARY')]:
        if not isinstance(doc, dict):
            errors.append(f'{label}目录必须是对象')
            continue
        if doc.get('scope') != scope:
            errors.append(f'{label}目录 scope 必须是 {scope}')
        _require_str(doc.get('catalog_version'), f'{label}目录 catalog_version', errors)
        _require_str(doc.get('source_id'), f'{label}目录 source_id', errors)
        if doc.get('review_status') not in REVIEW_STATUSES:
            errors.append(f'{label}目录 review_status 非法')
        items = doc.get(key)
        if not isinstance(items, list) or not items:
            errors.append(f'{label}目录 {key} 必须是非空列表')
    if errors:
        raise ContentError('内容目录校验失败', errors)
    seen_ids, seen_terms = set(), set()
    for lesson in lessons_doc['lessons']:
        validate_lesson(lesson, seen_ids)
    for term in glossary_doc['terms']:
        validate_glossary_term(term, seen_terms)
    return True


def load_content(content_dir=None):
    base = Path(content_dir) if content_dir else DEFAULT_CONTENT_DIR
    lessons_doc = _read_json(base / 'lessons' / 'lessons.json')
    glossary_doc = _read_json(base / 'glossary' / 'glossary.json')
    validate_catalog(lessons_doc, glossary_doc)
    return lessons_doc, glossary_doc


_LESSONS_DOC, _GLOSSARY_DOC = load_content()
LESSONS = list(_LESSONS_DOC['lessons'])
GLOSSARY = {item['term']: item['definition'] for item in _GLOSSARY_DOC['terms']}


def public_lesson(lesson):
    return {key: value for key, value in lesson.items() if key not in PUBLIC_LESSON_EXCLUDE}


def list_lessons(tag=None, q=None):
    out = []
    for lesson in LESSONS:
        if tag and lesson['tag'] != tag:
            continue
        if q and not any(q in str(lesson.get(field, '')) for field in ('title', 'body', 'question', 'tag')):
            continue
        out.append(public_lesson(lesson))
    return out


def get_lesson(lesson_id, include_answer=False):
    lesson = next((item for item in LESSONS if item['id'] == lesson_id), None)
    if lesson is None:
        raise ContentError(f'课程不存在：{lesson_id}', [f'课程不存在：{lesson_id}'])
    return dict(lesson) if include_answer else public_lesson(lesson)


def list_glossary(q=None):
    out = []
    for term in _GLOSSARY_DOC['terms']:
        if q and q not in term['term'] and q not in term['definition']:
            continue
        out.append({'term': term['term'], 'definition': term['definition'],
                    'version': _GLOSSARY_DOC['catalog_version'], 'scope': _GLOSSARY_DOC['scope'],
                    'source_id': _GLOSSARY_DOC['source_id'], 'review_status': _GLOSSARY_DOC['review_status']})
    return out


def lookup_terms(text):
    return [term for term in GLOSSARY if term in (text or '')]


def content_metadata():
    return {
        'catalog_version': VERSION,
        'lessons': {key: _LESSONS_DOC[key] for key in ('catalog_version', 'scope', 'origin', 'source_id', 'review_status')} | {'count': len(LESSONS)},
        'glossary': {key: _GLOSSARY_DOC[key] for key in ('catalog_version', 'scope', 'origin', 'source_id', 'review_status')} | {'count': len(_GLOSSARY_DOC['terms'])},
    }


def require_reviewed(doc, label):
    if doc.get('review_status') != 'REVIEWED':
        raise ContentError(f'{label}尚未通过审核，不能用于正式解释', [f'{label} review_status={doc.get("review_status")}'])
    return True


def reviewed_lesson(lesson_id):
    require_reviewed(_LESSONS_DOC, '课程内容')
    return get_lesson(lesson_id, include_answer=True)


router = APIRouter(prefix='/api/catalog', tags=['content-catalog'])


@router.get('/lessons')
def api_lessons(tag: str | None = None, q: str | None = None):
    return {'version': _LESSONS_DOC['catalog_version'], 'source_id': _LESSONS_DOC['source_id'],
            'review_status': _LESSONS_DOC['review_status'], 'lessons': list_lessons(tag, q)}


@router.get('/lessons/{lesson_id}')
def api_lesson(lesson_id: str, include_answer: bool = False):
    try:
        return {'lesson': get_lesson(lesson_id, include_answer)}
    except ContentError as exc:
        raise HTTPException(404, str(exc))


@router.get('/glossary')
def api_glossary(q: str | None = None):
    return {'version': _GLOSSARY_DOC['catalog_version'], 'source_id': _GLOSSARY_DOC['source_id'],
            'review_status': _GLOSSARY_DOC['review_status'], 'terms': list_glossary(q)}


@router.get('/metadata')
def api_metadata():
    return content_metadata()


@router.post('/validate')
def api_validate(body: dict):
    kind = body.get('kind')
    payload = body.get('payload')
    try:
        if kind == 'lesson':
            validate_lesson(payload)
        elif kind == 'glossary':
            validate_glossary_term(payload)
        else:
            return {'valid': False, 'reasons': [f'未知的校验类型：{kind}']}
    except ContentError as exc:
        return {'valid': False, 'reasons': exc.reasons}
    return {'valid': True, 'reasons': []}


def mount(app):
    app.include_router(router)
    return app

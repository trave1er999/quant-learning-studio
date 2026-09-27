"""Case catalog, query, comparison and validation tests.

Fixtures are synthetic/test-only; they prove code behaviour and do not represent
real fund cases or verified financial results.
"""
import json
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app import cases as cases_mod


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(cases_mod.router)
    with TestClient(app) as test_client:
        yield test_client


def valid_source(source_id='src-test-001', review_status='APPROVED'):
    return {'source_id': source_id, 'title': '测试来源', 'publisher': None, 'url': None, 'retrieved_at': '2026-09-27',
            'published': None, 'material_type': 'AUTHORED_LESSON', 'license': '项目自制测试', 'original_locator': 'test',
            'usable_for': ['DEV_CHECK'], 'review_status': review_status, 'return_reason': None}


def valid_case(case_id='case-test-001', source_id='src-test-001', **overrides):
    case = {'case_id': case_id, 'version': '1.0.0', 'market': 'CN', 'subject': '测试案例', 'object_type': 'SYNTHETIC_FIXTURE',
            'material_type': 'SYNTHETIC_SAMPLE', 'currency': 'CNY', 'period': {'start': '2024-01-02', 'end': '2024-12-31'},
            'source_id': source_id, 'known_fields': {'strategy_category': '测试'}, 'unknown_fields': ['realized_return'],
            'limitations': '仅供测试，不代表真实对象。', 'review_status': 'REVIEWED', 'return_reason': None}
    case.update(overrides)
    return case


def write_catalog(tmp_path, cases_doc, sources_doc, reviews_doc=None):
    base = Path(tmp_path)
    (base / 'cases').mkdir(parents=True, exist_ok=True)
    (base / 'cases' / 'cases.json').write_text(json.dumps(cases_doc, ensure_ascii=False), encoding='utf-8')
    (base / 'cases' / 'sources.json').write_text(json.dumps(sources_doc, ensure_ascii=False), encoding='utf-8')
    if reviews_doc is not None:
        (base / 'reviews').mkdir(parents=True, exist_ok=True)
        (base / 'reviews' / 'reviews.json').write_text(json.dumps(reviews_doc, ensure_ascii=False), encoding='utf-8')
    return base


def test_catalog_loads_and_distinguishes_object_types():
    types_seen = {case['object_type'] for case in cases_mod.CASES}
    assert cases_mod.OBJECT_TYPES[0] in types_seen
    assert cases_mod.OBJECT_TYPES[1] in types_seen
    assert cases_mod.OBJECT_TYPES[2] in types_seen
    for case in cases_mod.CASES:
        assert case['case_id'] and case['version'] and case['source_id']


def test_list_filters_by_market():
    cn = cases_mod.list_cases(market='CN')
    assert cn and all(row['market'] == 'CN' for row in cn)
    us = cases_mod.list_cases(market='US')
    assert us and all(row['market'] == 'US' for row in us)


def test_list_excludes_unreviewed_by_default_and_flags_pending():
    default_ids = {row['case_id'] for row in cases_mod.list_cases()}
    assert 'case-real-cn-pending' not in default_ids
    assert all(not row['needs_review'] for row in cases_mod.list_cases())
    pending = cases_mod.list_cases(include_pending=True)
    pending_row = next(row for row in pending if row['case_id'] == 'case-real-cn-pending')
    assert pending_row['needs_review'] is True


def test_explanation_view_never_returns_pending_even_when_included():
    ids = {row['case_id'] for row in cases_mod.list_cases(include_pending=True, for_explanation=True)}
    assert 'case-real-cn-pending' not in ids
    assert all(row['needs_review'] is False for row in cases_mod.list_cases(for_explanation=True))


def test_case_detail_binds_version_and_source():
    detail = cases_mod.get_case('case-authored-cn-01')
    assert detail['version_binding'] == {'case_id': 'case-authored-cn-01', 'version': '1.0.0',
                                         'source_id': 'src-authored-case-cn', 'source_registered': True}
    assert detail['source']['source_id'] == 'src-authored-case-cn'
    assert 'realized_return' in detail['unknown_fields']
    assert detail['known_fields'] and detail['limitations']


def test_unknown_case_raises_not_found():
    with pytest.raises(cases_mod.CaseNotFound):
        cases_mod.get_case('case-does-not-exist')


def test_rejected_case_denied_even_with_pending():
    with pytest.raises(cases_mod.CasePermissionError):
        cases_mod.get_case('case-real-us-rejected')
    with pytest.raises(cases_mod.CasePermissionError):
        cases_mod.get_case('case-real-us-rejected', include_pending=True)


def test_pending_case_not_for_formal_explanation():
    with pytest.raises(cases_mod.CasePermissionError):
        cases_mod.get_case('case-real-cn-pending')
    with pytest.raises(cases_mod.CasePermissionError):
        cases_mod.get_case('case-real-cn-pending', for_explanation=True)
    assert cases_mod.get_case('case-real-cn-pending', include_pending=True)['needs_review'] is True


def test_compare_returns_comparable_descriptive_fields():
    result = cases_mod.compare_cases('case-authored-cn-01', 'case-fixture-cn-01')
    fields = {row['field'] for row in result['comparable']}
    assert {'market', 'currency', 'strategy_category', 'fee_model'} <= fields
    assert result['incomparable'] == []


def test_compare_currency_mismatch_is_incomparable():
    result = cases_mod.compare_cases('case-authored-cn-01', 'case-authored-us-01')
    reasons = {row['reason'] for row in result['incomparable']}
    assert 'CURRENCY_MISMATCH' in reasons
    amounts = [row for row in result['comparable'] if row['field'] in cases_mod.AMOUNT_FIELDS]
    assert amounts == []


def test_compare_period_mismatch_is_incomparable():
    result = cases_mod.compare_cases('case-authored-us-01', 'case-authored-us-02')
    reasons = {row['reason'] for row in result['incomparable']}
    assert 'PERIOD_MISMATCH' in reasons


def test_compare_missing_source_is_incomparable():
    result = cases_mod.compare_cases('case-real-cn-pending', 'case-real-us-pending', include_pending=True)
    reasons = {row['reason'] for row in result['incomparable']}
    assert 'SOURCE_UNRESOLVED' in reasons


def test_compare_unknown_fields_are_not_filled():
    result = cases_mod.compare_cases('case-authored-cn-01', 'case-fixture-cn-01')
    unknown_fields = {(row['field'], row['side']) for row in result['unknown']}
    assert ('realized_return', 'left') in unknown_fields
    assert ('fund_net_value', 'right') in unknown_fields


def test_compare_never_returns_computed_metrics():
    result = cases_mod.compare_cases('case-authored-cn-01', 'case-authored-us-01')
    blob = json.dumps(result, ensure_ascii=False)
    assert 'total_return' not in blob and 'ending' not in blob
    assert result['metric_reference']['provider'] == 'yu-wei'
    assert result['metric_reference']['status'] != 'DONE'


def test_compare_rejects_unknown_case():
    with pytest.raises(cases_mod.CaseNotFound):
        cases_mod.compare_cases('case-authored-cn-01', 'nope')


def test_validate_case_missing_required_field():
    bad = valid_case()
    bad.pop('subject')
    with pytest.raises(cases_mod.CaseError) as exc:
        cases_mod.validate_case(bad, {'src-test-001'})
    assert any('subject' in reason for reason in exc.value.reasons)


def test_validate_case_duplicate_id():
    seen = set()
    cases_mod.validate_case(valid_case(), {'src-test-001'}, seen)
    with pytest.raises(cases_mod.CaseError) as exc:
        cases_mod.validate_case(valid_case(), {'src-test-001'}, seen)
    assert any('重复' in reason for reason in exc.value.reasons)


def test_validate_case_market_currency_and_version():
    for overrides in ({'market': 'JP'}, {'currency': 'USD'}, {'version': '1.0'},
                      {'object_type': 'FUND'}, {'review_status': 'MAYBE'}):
        with pytest.raises(cases_mod.CaseError):
            cases_mod.validate_case(valid_case(**overrides), {'src-test-001'})


def test_validate_case_future_period_and_overlap():
    from datetime import date, timedelta
    future = (date.today() + timedelta(days=30)).isoformat()
    with pytest.raises(cases_mod.CaseError):
        cases_mod.validate_case(valid_case(period={'start': '2024-01-02', 'end': future}), {'src-test-001'})
    with pytest.raises(cases_mod.CaseError):
        cases_mod.validate_case(valid_case(known_fields={'realized_return': 'x'}, unknown_fields=['realized_return']), {'src-test-001'})


def test_validate_case_rejects_unregistered_source():
    with pytest.raises(cases_mod.CaseError) as exc:
        cases_mod.validate_case(valid_case(source_id='src-missing'), {'src-test-001'})
    assert any('未登记的来源' in reason for reason in exc.value.reasons)


def test_client_approval_cannot_override_server_review():
    payload = valid_case(case_id='case-new-001', source_id='src-authored-case-cn', review_status='REVIEWED', approved=True, accepted=True)
    result = cases_mod.validate_submission(payload)
    assert result['valid'] is True
    assert result['normalized']['review_status'] == 'UNREVIEWED'
    assert 'approved' not in result['normalized'] and 'accepted' not in result['normalized']
    assert len(result['warnings']) == 3


def test_validate_submission_reports_reasons():
    payload = valid_case(case_id='case-new-002')
    payload['market'] = 'JP'
    result = cases_mod.validate_submission(payload)
    assert result['valid'] is False and result['reasons']


def test_validate_reviews_requires_locator_for_accepted():
    with pytest.raises(cases_mod.CaseError):
        cases_mod.validate_reviews({'review_log_version': '1.0.0',
                                    'records': [{'review_id': 'r1', 'target_type': 'CASE', 'target': 'case-authored-cn-01',
                                                 'decision': 'ACCEPTED'}], 'queue': []})
    with pytest.raises(cases_mod.CaseError):
        cases_mod.validate_reviews({'review_log_version': '1.0.0',
                                    'records': [{'review_id': 'r2', 'decision': 'RETURNED'}], 'queue': []})


def test_load_catalog_rejects_bad_temp_files(tmp_path):
    write_catalog(tmp_path, {'catalog_version': '1.0.0', 'cases': [valid_case()]},
                  {'registry_version': '1.0.0', 'sources': [valid_source()]})
    cases_doc, sources_doc = cases_mod.load_catalog(tmp_path)
    assert cases_doc['cases'][0]['case_id'] == 'case-test-001'
    bad = valid_case()
    del bad['limitations']
    write_catalog(tmp_path, {'catalog_version': '1.0.0', 'cases': [bad]},
                  {'registry_version': '1.0.0', 'sources': [valid_source()]})
    with pytest.raises(cases_mod.CaseError):
        cases_mod.load_catalog(tmp_path)


def test_review_records_and_queue_exposed():
    data = cases_mod.review_records()
    assert data['records'] and data['queue']
    assert any(record['decision'] == 'RETURNED' for record in data['records'])
    assert all(item['status'] == 'AWAITING_SUBMISSION' for item in data['queue'])


def test_http_cases_list_and_filter(client):
    body = client.get('/api/catalog/cases', params={'market': 'CN'}).json()
    assert body['cases'] and all(row['market'] == 'CN' for row in body['cases'])
    assert client.get('/api/catalog/cases', params={'market': 'XX'}).status_code == 422


def test_http_case_detail_not_found_and_forbidden(client):
    ok = client.get('/api/catalog/cases/case-authored-cn-01')
    assert ok.status_code == 200 and ok.json()['case']['version'] == '1.0.0'
    assert client.get('/api/catalog/cases/case-missing').status_code == 404
    assert client.get('/api/catalog/cases/case-real-us-rejected').status_code == 403


def test_http_compare_and_metadata(client):
    result = client.get('/api/catalog/compare', params={'left': 'case-authored-cn-01', 'right': 'case-authored-us-01'}).json()
    assert any(row['reason'] == 'CURRENCY_MISMATCH' for row in result['incomparable'])
    assert client.get('/api/catalog/compare', params={'left': 'case-authored-cn-01', 'right': 'x'}).status_code == 404
    assert client.get('/api/catalog/markets').status_code == 200
    assert client.get('/api/catalog/sources').status_code == 200
    assert client.get('/api/catalog/reviews').status_code == 200


def test_http_validate_case_ignores_client_approval(client):
    payload = valid_case(case_id='case-http-001', source_id='src-authored-case-cn', approved=True)
    body = client.post('/api/catalog/validate/case', json=payload).json()
    assert body['valid'] is True
    assert body['normalized']['review_status'] == 'UNREVIEWED'
    assert body['warnings']
    bad = valid_case(case_id='case-http-002', market='JP')
    assert client.post('/api/catalog/validate/case', json=bad).json()['valid'] is False

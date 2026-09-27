"""CN/US case catalog: structure, query, comparison and input validation.

This is a read-only service. It never computes returns, fees or risk numbers:
those figures come from Yu's deterministic engine through the
market_snapshot/metrics interface. Unreviewed or rejected material is not served
for formal explanation, and client-supplied "approved" flags never replace the
server-side review state.
"""
from __future__ import annotations
import json, os, re
from datetime import date
from pathlib import Path
from fastapi import APIRouter, HTTPException

VERSION = 'qlab-cases-catalog-1.0.0'
ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONTENT_DIR = Path(os.environ.get('QLAB_CONTENT_DIR', str(ROOT / 'content')))

MARKETS = ('CN', 'US')
MARKET_CURRENCY = {'CN': 'CNY', 'US': 'USD'}
OBJECT_TYPES = ('PRIVATE_FUND_REAL', 'TEACHING_STRATEGY', 'SYNTHETIC_FIXTURE')
MATERIAL_TYPES = ('PUBLIC_DISCLOSURE', 'AUTHORED_LESSON', 'SYNTHETIC_SAMPLE')
REVIEW_STATUSES = ('REVIEWED', 'UNREVIEWED', 'REJECTED')
SOURCE_REVIEW_STATUSES = ('APPROVED', 'AWAITING_SOURCE', 'REJECTED')
REVIEW_DECISIONS = ('ACCEPTED', 'RETURNED')
VERSION_PATTERN = re.compile(r'\d+\.\d+\.\d+')

CASE_REQUIRED = ['case_id', 'version', 'market', 'subject', 'object_type', 'material_type',
                 'currency', 'source_id', 'known_fields', 'unknown_fields', 'limitations', 'review_status']
SOURCE_REQUIRED = ['source_id', 'title', 'material_type', 'license', 'usable_for', 'review_status']
CLIENT_REVIEW_FIELDS = ('review_status', 'approved', 'accepted', 'verification', 'server_review', 'reviewed')

AMOUNT_FIELDS = ('fund_net_value', 'realized_return', 'drawdown_history', 'fee_paid')
PERIOD_DEPENDENT_FIELDS = ('realized_return', 'drawdown_history', 'fee_paid')
TOP_LEVEL_FIELDS = {'market': 'market', 'currency': 'currency',
                    'material_type': 'material_type', 'object_type': 'object_type'}
DESCRIPTIVE_FIELDS = ('market', 'currency', 'material_type', 'object_type',
                      'strategy_category', 'risk_control', 'fee_model')
COMPARE_FIELDS = DESCRIPTIVE_FIELDS + AMOUNT_FIELDS
METRIC_REFERENCE = {
    'provider': 'yu-wei',
    'interface': 'market_snapshot.metrics',
    'status': 'EXTERNAL_NOT_IMPLEMENTED',
    'note': '收益、风险与费用数值由 Yu 的确定性引擎提供；本模块只判断口径与可比性，不自行计算。',
}


class CaseError(ValueError):
    def __init__(self, message, reasons=None):
        reasons = list(reasons) if reasons else [message]
        super().__init__(message)
        self.reasons = reasons


class CaseNotFound(CaseError):
    pass


class CasePermissionError(CaseError):
    pass


def _read_json(path):
    path = Path(path)
    try:
        with open(path, encoding='utf-8') as handle:
            data = json.load(handle)
    except FileNotFoundError:
        raise CaseError(f'缺少案例文件：{path.name}', [f'缺少案例文件：{path}'])
    except json.JSONDecodeError as exc:
        raise CaseError(f'案例文件不是合法 JSON：{path.name}', [f'案例文件不是合法 JSON：{path}（{exc.msg}）'])
    if not isinstance(data, dict):
        raise CaseError(f'案例文件根节点必须是对象：{path.name}', [f'案例文件根节点必须是对象：{path}'])
    return data


def _require_str(value, field, errors):
    if not isinstance(value, str) or not value.strip():
        errors.append(f'字段 {field} 必须是非空字符串')


def validate_period(period, errors, today=None):
    if period is None:
        return
    today = today or date.today()
    if not isinstance(period, dict) or 'start' not in period or 'end' not in period:
        errors.append('字段 period 必须是含 start/end 的对象或 null')
        return
    try:
        start = date.fromisoformat(str(period['start']))
        end = date.fromisoformat(str(period['end']))
    except (ValueError, TypeError):
        errors.append('字段 period 的日期必须是 ISO 格式')
        return
    if start > end:
        errors.append('字段 period 的开始日期不能晚于结束日期')
    if end > today:
        errors.append('字段 period 的结束日期不能在未来')


def validate_source(source, seen_ids=None):
    errors = []
    if not isinstance(source, dict):
        raise CaseError('来源条目必须是对象', ['来源条目必须是对象'])
    for field in SOURCE_REQUIRED:
        if field not in source:
            errors.append(f'来源缺少必填字段 {field}')
    _require_str(source.get('source_id'), 'source_id', errors)
    _require_str(source.get('title'), 'title', errors)
    if source.get('material_type') not in MATERIAL_TYPES:
        errors.append('来源 material_type 非法')
    if source.get('review_status') not in SOURCE_REVIEW_STATUSES:
        errors.append('来源 review_status 非法')
    if not isinstance(source.get('usable_for'), list):
        errors.append('来源 usable_for 必须是列表')
    if source.get('review_status') == 'REJECTED' and not source.get('return_reason'):
        errors.append('被退回的来源必须说明退回原因')
    source_id = source.get('source_id')
    if seen_ids is not None and isinstance(source_id, str) and source_id.strip():
        if source_id in seen_ids:
            errors.append(f'来源 id 重复：{source_id}')
        seen_ids.add(source_id)
    if errors:
        raise CaseError('来源校验失败', errors)
    return True


def validate_case(case, source_ids=None, seen_ids=None, today=None):
    errors = []
    if not isinstance(case, dict):
        raise CaseError('案例条目必须是对象', ['案例条目必须是对象'])
    for field in CASE_REQUIRED:
        if field not in case:
            errors.append(f'案例缺少必填字段 {field}')
    _require_str(case.get('case_id'), 'case_id', errors)
    _require_str(case.get('subject'), 'subject', errors)
    _require_str(case.get('limitations'), 'limitations', errors)
    version = case.get('version')
    if not isinstance(version, str) or not VERSION_PATTERN.fullmatch(version):
        errors.append('字段 version 必须是形如 1.0.0 的版本号')
    market = case.get('market')
    if market not in MARKETS:
        errors.append('字段 market 必须是 CN 或 US')
    currency = case.get('currency')
    if market in MARKET_CURRENCY and currency != MARKET_CURRENCY[market]:
        errors.append('字段 currency 必须与 market 匹配（CN=CNY，US=USD）')
    if case.get('object_type') not in OBJECT_TYPES:
        errors.append('字段 object_type 非法')
    if case.get('material_type') not in MATERIAL_TYPES:
        errors.append('字段 material_type 非法')
    if case.get('review_status') not in REVIEW_STATUSES:
        errors.append('字段 review_status 非法')
    known, unknown = case.get('known_fields'), case.get('unknown_fields')
    if not isinstance(known, dict):
        errors.append('字段 known_fields 必须是对象')
        known = {}
    if not isinstance(unknown, list) or any(not isinstance(x, str) or not x.strip() for x in unknown):
        errors.append('字段 unknown_fields 必须是字符串列表')
        unknown = []
    overlap = set(known) & set(unknown)
    if overlap:
        errors.append('known_fields 与 unknown_fields 不能重叠：' + ','.join(sorted(overlap)))
    validate_period(case.get('period'), errors, today)
    source_id = case.get('source_id')
    _require_str(source_id, 'source_id', errors)
    if source_ids is not None and isinstance(source_id, str) and source_id not in source_ids:
        errors.append(f'引用了未登记的来源：{source_id}')
    case_id = case.get('case_id')
    if seen_ids is not None and isinstance(case_id, str) and case_id.strip():
        if case_id in seen_ids:
            errors.append(f'案例 id 重复：{case_id}')
        seen_ids.add(case_id)
    if errors:
        raise CaseError('案例校验失败', errors)
    return True


def validate_cases(cases_doc, sources_doc, today=None):
    errors = []
    if not isinstance(cases_doc, dict) or not isinstance(cases_doc.get('cases'), list) or not cases_doc['cases']:
        raise CaseError('案例目录校验失败', ['cases 必须是非空列表'])
    _require_str(cases_doc.get('catalog_version'), 'cases.catalog_version', errors)
    if errors:
        raise CaseError('案例目录校验失败', errors)
    source_ids = {s['source_id'] for s in sources_doc['sources'] if isinstance(s, dict) and isinstance(s.get('source_id'), str)}
    seen = set()
    for case in cases_doc['cases']:
        validate_case(case, source_ids, seen, today)
    return True


def validate_reviews(reviews_doc, case_ids=None):
    errors = []
    if not isinstance(reviews_doc, dict):
        raise CaseError('复核记录必须是对象', ['复核记录必须是对象'])
    _require_str(reviews_doc.get('review_log_version'), 'review_log_version', errors)
    for key in ('records', 'queue'):
        if not isinstance(reviews_doc.get(key), list):
            errors.append(f'{key} 必须是列表')
    if errors:
        raise CaseError('复核记录校验失败', errors)
    for record in reviews_doc['records']:
        if not isinstance(record, dict) or record.get('decision') not in REVIEW_DECISIONS:
            errors.append('复核记录 decision 非法')
            continue
        if record['decision'] == 'ACCEPTED':
            for field in ('locator', 'purpose', 'license', 'available_from'):
                if not record.get(field):
                    errors.append(f'通过的复核记录必须填写 {field}')
        elif not record.get('reason'):
            errors.append('退回的复核记录必须说明原因')
        if case_ids is not None and record.get('target_type') == 'CASE' and record.get('target') not in case_ids:
            errors.append(f'复核记录了未知案例：{record.get("target")}')
    if errors:
        raise CaseError('复核记录校验失败', errors)
    return True


def load_catalog(content_dir=None, today=None):
    base = Path(content_dir) if content_dir else DEFAULT_CONTENT_DIR
    cases_doc = _read_json(base / 'cases' / 'cases.json')
    sources_doc = _read_json(base / 'cases' / 'sources.json')
    seen = set()
    if not isinstance(sources_doc, dict) or not isinstance(sources_doc.get('sources'), list) or not sources_doc['sources']:
        raise CaseError('来源登记校验失败', ['sources 必须是非空列表'])
    for source in sources_doc['sources']:
        validate_source(source, seen)
    validate_cases(cases_doc, sources_doc, today)
    return cases_doc, sources_doc


def load_reviews(content_dir=None, case_ids=None):
    base = Path(content_dir) if content_dir else DEFAULT_CONTENT_DIR
    reviews_doc = _read_json(base / 'reviews' / 'reviews.json')
    validate_reviews(reviews_doc, case_ids)
    return reviews_doc


_CASES_DOC, _SOURCES_DOC = load_catalog()
CASES = list(_CASES_DOC['cases'])
SOURCES = {source['source_id']: source for source in _SOURCES_DOC['sources']}
_REVIEWS_DOC = load_reviews(case_ids={c['case_id'] for c in CASES})


def resolve_source(source_id):
    return SOURCES.get(source_id)


def _is_served(case, include_pending, for_explanation):
    if case['review_status'] == 'REJECTED':
        return False
    if for_explanation:
        return case['review_status'] == 'REVIEWED'
    if case['review_status'] == 'REVIEWED':
        return True
    return include_pending


def case_summary(case):
    return {key: case.get(key) for key in ('case_id', 'version', 'market', 'subject', 'object_type',
                                           'material_type', 'currency', 'period', 'source_id', 'review_status')}


def list_cases(market=None, object_type=None, source_id=None, include_pending=False, for_explanation=False):
    out = []
    for case in CASES:
        if market and case['market'] != market:
            continue
        if object_type and case['object_type'] != object_type:
            continue
        if source_id and case['source_id'] != source_id:
            continue
        if not _is_served(case, include_pending, for_explanation):
            continue
        summary = case_summary(case)
        summary['needs_review'] = case['review_status'] != 'REVIEWED'
        out.append(summary)
    return out


def find_case(case_id):
    return next((case for case in CASES if case['case_id'] == case_id), None)


def get_case(case_id, include_pending=False, for_explanation=False):
    case = find_case(case_id)
    if case is None:
        raise CaseNotFound(f'案例不存在：{case_id}', [f'案例不存在：{case_id}'])
    if case['review_status'] == 'REJECTED':
        raise CasePermissionError(f'案例已退回，不对外提供：{case_id}', [f'{case_id} review_status=REJECTED'])
    if not _is_served(case, include_pending, for_explanation):
        raise CasePermissionError(f'案例尚未通过审核，不能用于正式解释：{case_id}', [f'{case_id} review_status={case["review_status"]}'])
    source = resolve_source(case['source_id'])
    detail = case_summary(case)
    detail.update({
        'known_fields': case.get('known_fields', {}),
        'unknown_fields': case.get('unknown_fields', []),
        'limitations': case.get('limitations'),
        'return_reason': case.get('return_reason'),
        'source': source,
        'version_binding': {'case_id': case['case_id'], 'version': case['version'], 'source_id': case['source_id'],
                            'source_registered': source is not None},
        'needs_review': case['review_status'] != 'REVIEWED',
    })
    return detail


def _field_value(case, field):
    if field in TOP_LEVEL_FIELDS:
        return case.get(TOP_LEVEL_FIELDS[field])
    if field in case.get('unknown_fields', []):
        return None
    return case.get('known_fields', {}).get(field)


def _period_pair(case):
    period = case.get('period')
    if isinstance(period, dict) and period.get('start') and period.get('end'):
        return (period['start'], period['end'])
    return None


def compare_cases(left_id, right_id, include_pending=False):
    left = find_case(left_id)
    right = find_case(right_id)
    if left is None:
        raise CaseNotFound(f'案例不存在：{left_id}', [f'案例不存在：{left_id}'])
    if right is None:
        raise CaseNotFound(f'案例不存在：{right_id}', [f'案例不存在：{right_id}'])
    for case in (left, right):
        if case['review_status'] == 'REJECTED':
            raise CasePermissionError(f'案例已退回，不参与比较：{case["case_id"]}', [f'{case["case_id"]} review_status=REJECTED'])
        if not _is_served(case, include_pending, False):
            raise CasePermissionError(f'案例尚未通过审核，不参与比较：{case["case_id"]}', [f'{case["case_id"]} review_status={case["review_status"]}'])

    incomparable, unknown, comparable = [], [], []
    for case, side in ((left, 'left'), (right, 'right')):
        source = resolve_source(case['source_id'])
        if source is None or source.get('review_status') != 'APPROVED':
            incomparable.append({'field': 'source', 'reason': 'SOURCE_UNRESOLVED',
                                 'detail': f'{side} 侧来源未登记或未通过复核，来源相关结论不得用于比较。',
                                 'side': side})

    left_period, right_period = _period_pair(left), _period_pair(right)
    currency_mismatch = left['currency'] != right['currency']
    period_mismatch = left_period is not None and right_period is not None and left_period != right_period
    if currency_mismatch:
        incomparable.append({'field': 'amounts', 'reason': 'CURRENCY_MISMATCH', 'side': 'both',
                             'detail': f"{left['currency']} 与 {right['currency']} 金额不可直接相加或比较；不换算汇率。"})
    if period_mismatch:
        incomparable.append({'field': 'period_metrics', 'reason': 'PERIOD_MISMATCH', 'side': 'both',
                             'detail': '两案例期间不同，期间相关数值不可直接比较。'})

    for field in COMPARE_FIELDS:
        left_value, right_value = _field_value(left, field), _field_value(right, field)
        if left_value is None or right_value is None:
            if left_value is None:
                unknown.append({'field': field, 'side': 'left', 'reason': 'UNKNOWN', 'detail': '该侧未获核验，不补值。'})
            if right_value is None:
                unknown.append({'field': field, 'side': 'right', 'reason': 'UNKNOWN', 'detail': '该侧未获核验，不补值。'})
            continue
        if field in AMOUNT_FIELDS and currency_mismatch:
            continue
        if field in PERIOD_DEPENDENT_FIELDS and period_mismatch:
            continue
        comparable.append({'field': field, 'left': left_value, 'right': right_value})

    return {
        'left': case_summary(left),
        'right': case_summary(right),
        'comparable': comparable,
        'unknown': unknown,
        'incomparable': incomparable,
        'metric_reference': METRIC_REFERENCE,
        'notice': '可比字段用于说明资料口径；收益、风险与费用数值由 Yu 的引擎提供，本模块不计算，也不因缺失字段判定胜负。',
    }


def markets_summary():
    out = []
    for market in MARKETS:
        rows = [case for case in CASES if case['market'] == market]
        out.append({'market': market, 'currency': MARKET_CURRENCY[market], 'total': len(rows),
                    'reviewed': sum(1 for r in rows if r['review_status'] == 'REVIEWED'),
                    'pending': sum(1 for r in rows if r['review_status'] == 'UNREVIEWED')})
    return out


def sources_list():
    return [{'source_id': s['source_id'], 'publisher': s.get('publisher'), 'title': s['title'], 'url': s.get('url'),
             'material_type': s['material_type'], 'license': s.get('license'), 'review_status': s['review_status'],
             'usable_for': s.get('usable_for')} for s in _SOURCES_DOC['sources']]


def review_records():
    return {'records': _REVIEWS_DOC['records'], 'queue': _REVIEWS_DOC['queue'], 'review_log_version': _REVIEWS_DOC['review_log_version']}


def validate_submission(payload):
    reasons, warnings = [], []
    if not isinstance(payload, dict):
        return {'valid': False, 'reasons': ['提交内容必须是对象'], 'warnings': [], 'normalized': None}
    normalized = dict(payload)
    for field in CLIENT_REVIEW_FIELDS:
        if field in normalized:
            warnings.append(f'客户端字段 {field} 不具权威性，已忽略；审核状态只能由服务端设置。')
            normalized.pop(field)
    normalized['review_status'] = 'UNREVIEWED'
    try:
        validate_case(normalized, set(SOURCES))
    except CaseError as exc:
        reasons.extend(exc.reasons)
    return {'valid': not reasons, 'reasons': reasons, 'warnings': warnings, 'normalized': normalized}


router = APIRouter(prefix='/api/catalog', tags=['case-catalog'])


@router.get('/cases')
def api_cases(market: str | None = None, object_type: str | None = None, source_id: str | None = None,
              include_pending: bool = False, for_explanation: bool = False):
    if market and market not in MARKETS:
        raise HTTPException(422, 'market 必须是 CN 或 US')
    if object_type and object_type not in OBJECT_TYPES:
        raise HTTPException(422, 'object_type 非法')
    return {'catalog_version': _CASES_DOC['catalog_version'],
            'cases': list_cases(market, object_type, source_id, include_pending, for_explanation)}


@router.get('/cases/{case_id}')
def api_case(case_id: str, include_pending: bool = False, for_explanation: bool = False):
    try:
        return {'case': get_case(case_id, include_pending, for_explanation)}
    except CaseNotFound as exc:
        raise HTTPException(404, str(exc))
    except CasePermissionError as exc:
        raise HTTPException(403, str(exc))


@router.get('/markets')
def api_markets():
    return {'markets': markets_summary()}


@router.get('/sources')
def api_sources():
    return {'registry_version': _SOURCES_DOC['registry_version'], 'sources': sources_list()}


@router.get('/compare')
def api_compare(left: str, right: str, include_pending: bool = False):
    try:
        return compare_cases(left, right, include_pending)
    except CaseNotFound as exc:
        raise HTTPException(404, str(exc))
    except CasePermissionError as exc:
        raise HTTPException(403, str(exc))


@router.get('/reviews')
def api_reviews():
    return review_records()


@router.post('/validate/case')
def api_validate_case(body: dict):
    return validate_submission(body)


def mount(app):
    app.include_router(router)
    return app

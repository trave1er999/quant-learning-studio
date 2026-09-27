# Xiangze.Zhu 接口请求单（XZ-06 接入）

本人模块不修改共享入口与页面。以下为最小接入请求，均由对应负责人执行；本人提供代码与 `mount(app)`，不擅自扩大范围。

## 1. 给 Yu.Wei（owner，公共入口与共享契约）

**a) 挂载只读目录路由**（`app/main.py`）。路由必须在 catch-all `@app.get('/{path:path}')` **之前**注册，否则会被通配路由吞掉：

```python
from app import cases as cases_module, content as content_module
# 放在 initialize() 之前或紧随其后、且在 index 通配路由之前
cases_module.mount(app)
content_module.mount(app)
```

**b) 冻结 `market_snapshot.metrics` 接口**，供比较服务取数值（本人不自行计算）。最小字段：`snapshot_id`、`instrument`、`market`、`currency`、`period`、`metric`、`value`、`version`。本人比较结果对象中的 `metric_reference` 已预留该引用：`{'provider':'yu-wei','interface':'market_snapshot.metrics','status':'EXTERNAL_NOT_IMPLEMENTED'}`。

**c) 按 ACCESS_MODEL 批准本 PLAN**（blob SHA + 精确路径）：`app/content.py`、`app/cases.py`、`tests/test_cases.py`、`tests/test_content.py`，文档 `content/cases/`、`content/lessons/`、`content/glossary/`、`content/reviews/`、`evidence/xiangze-zhu/`。批准前 `scope_active=false`，本人实施 PR 不满足门禁。

## 2. 给 Zaixuan.Ji（UI 与原比较页/资料页）

保留既有 UI，仅新增必要控件并调用只读接口：
- 比较页：`GET /api/catalog/cases?market=CN|US` 选择案例；`GET /api/catalog/cases/{case_id}` 展示 `known_fields`/`unknown_fields`/`limitations` 与 `source`；`GET /api/catalog/compare?left=&right=` 展示 `comparable`/`unknown`/`incomparable`（不可比原因如 `CURRENCY_MISMATCH`/`PERIOD_MISMATCH`/`SOURCE_UNRESOLVED`）。
- 未审核内容：默认接口不返回；`?include_pending=true` 才返回并带 `needs_review=true`，UI 需明确标注“待核验，不用于正式解释”；被退回内容返回 403，不展示。
- 风格、导航与组件归 Zaixuan；本人不接管 `web/`。

## 3. 给 Tianqi.Hao（检索 / F2 策划 / F4 复盘上下文）

- 教学依据：`GET /api/catalog/lessons`、`/lessons/{id}`（含 `version`/`source_id`/`review_status`）、`GET /api/catalog/glossary`；术语定位可用 `app.content.lookup_terms(text)`。
- 案例依据：`GET /api/catalog/cases/{case_id}` 返回带 `version_binding` 的记录，作为当时依据时必须同时保存 `case_id`/`version`/`source_id`。
- 只使用 `review_status=REVIEWED` 的内容；本模块不生成 AI 文本、不保存学生作答与报告（属 Tianqi）。

## 4. 给 Yifan.Mao / Guanjie.Xue / Yuntao.Min（资料与真人测试）

按 `templates/SOURCE_CARD.md` 提交资料卡到 `research/submissions/<role>/`，含原文定位（PDF 页/章节）、用途（PRE_PLAN / POST_RUN_LEARNING / DEVELOPMENT_REFERENCE）、许可状态与可得时间。本人按 XZ-05 复核并记录 `content/reviews/reviews.json`；许可不清或定位缺失将退回并写明原因，不使用未审来源。

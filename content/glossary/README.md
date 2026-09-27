# 案例与教学内容 · R3

Xiangze.Zhu 负责术语内容的数据与读取/筛选/校验；代码为 `app/content.py`。

## 文件格式 `glossary.json`

顶层：`catalog_version`、`scope`（必须为 `GLOSSARY`）、`origin`、`source_id`、`review_status`、`terms`（非空列表）。

每个 `term`：`term`、`definition`（均为非空字符串）。重复 `term`、缺字段会被 `validate_glossary_term` 拒绝。`list_glossary(q)` 与 `/api/catalog/glossary` 返回带 `version`/`scope`/`source_id`/`review_status` 的结构化条目；`lookup_terms(text)` 用于在解释文本中定位术语。

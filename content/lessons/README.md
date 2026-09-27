# 案例与教学内容 · R3

Xiangze.Zhu 负责学习目录的数据与读取/筛选/校验；代码为 `app/content.py`。学生作答、进度、AI 与报告流程由 Tianqi 负责。

## 文件格式 `lessons.json`

顶层：`catalog_version`、`scope`（必须为 `LESSON`）、`origin`、`source_id`、`review_status`（`REVIEWED`/`UNREVIEWED`/`REJECTED`）、`lessons`（非空列表）。

每个 `lesson`：`id`、`title`、`minutes`（正整数）、`tag`、`body`、`question`、`options`（≥2 项非空字符串）、`answer`（整数索引且在范围内）、`explanation`。

公开视图（`list_lessons`、`/api/catalog/lessons`）隐藏 `answer` 与 `explanation`；服务端解释使用 `get_lesson(id, include_answer=True)`。重复 `id`、缺字段、非法范围会被 `validate_lesson` 拒绝。仅 `review_status=REVIEWED` 的内容可用于正式解释（`require_reviewed`）。

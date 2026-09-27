# 案例与教学内容 · R3

Xiangze.Zhu 负责相关内容结构、来源校验及实际模块代码/接口/测试。代码为 `app/cases.py`；服务路由挂载后位于 `/api/catalog/*`。未审来源、未知字段、模拟与真实记录必须区分。

## 文件格式

- `sources.json`：来源登记。每条含 `source_id`、`title`、`publisher`、`url`、`retrieved_at`、`published`、`material_type`（`PUBLIC_DISCLOSURE`/`AUTHORED_LESSON`/`SYNTHETIC_SAMPLE`）、`license`、`original_locator`、`usable_for`、`review_status`（`APPROVED`/`AWAITING_SOURCE`/`REJECTED`）、`return_reason`。
- `cases.json`：案例目录。每条含 `case_id`、`version`（`x.y.z`）、`market`（`CN`/`US`）、`subject`、`object_type`（`PRIVATE_FUND_REAL`/`TEACHING_STRATEGY`/`SYNTHETIC_FIXTURE`）、`material_type`、`currency`（与市场匹配）、`period`、`source_id`、`known_fields`、`unknown_fields`、`limitations`、`review_status`（`REVIEWED`/`UNREVIEWED`/`REJECTED`）、`return_reason`。

约束：`known_fields` 与 `unknown_fields` 不得重叠；`source_id` 必须已在 `sources.json` 登记；`currency` 必须与 `market` 匹配；期间不得晚于今天。未知字段一律返回 `UNKNOWN`，不补值；真实基金业绩不得用模拟数字填补。

开发 fixture 与教学说明只用于代码/接口检查，不代表真实对象；真实中美私募案例必须由后三人提交原始资料卡并通过复核后入库。校验入口：`app.cases.validate_case` / `validate_cases` / `validate_submission`（客户端 `approved` 等字段不具权威性）。

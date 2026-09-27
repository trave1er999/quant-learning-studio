# 案例与教学内容 · R3

Xiangze.Zhu 负责接收并复核后三人（Yifan.Mao、Guanjie.Xue、Yuntao.Min）提交的资料卡，记录原文定位、用途、许可、可得时间与退回原因。复核记录存于 `reviews.json`，由 `app.cases.validate_reviews` 校验；入库/解析/索引使用 Zaixuan 的统一存储，本人通过 `source_id` 关联，不另建向量库。

## 文件格式 `reviews.json`

- 顶层：`review_log_version`、`last_updated`、`records`（列表）、`queue`（列表）。
- `records[]`：`review_id`、`target`、`target_type`（`AUTHORED_CONTENT`/`CASE`）、`submitter_role`、`received_at`、`locator`（原文定位）、`purpose`（`PRE_PLAN`/`POST_RUN_LEARNING`/`DEVELOPMENT_REFERENCE`）、`license`、`available_from`、`decision`（`ACCEPTED`/`RETURNED`）、`reason`。
- `queue[]`：`queue_id`、`submitter_role`、`expected`、`status`（如 `AWAITING_SUBMISSION`）、`received_at`。

约束：`ACCEPTED` 必须填写 `locator`/`purpose`/`license`/`available_from`；`RETURNED` 必须写明 `reason`；`target_type=CASE` 的 `target` 必须是已登记案例。资料交 Zaixuan 统一入库；已有贡献保留原作者、收件时间与代录者，不冒充资料人员写代码。当前队列三人均 `AWAITING_SUBMISSION`，尚无真实资料可入库。

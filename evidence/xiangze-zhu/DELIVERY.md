# 开发交付记录｜Xiangze.Zhu（R3）

- 角色/任务Issue：开发 · [#4](https://github.com/suiyisuixing/quant-learning-studio/issues/4)
- 基线commit、提交commit、PR：基线 `bootstrap/r3-collaboration` d9082869be5714b09e2587107359f4acc91426d1（main 57cf025…，PR #20 未合并）；提交见 git log（本分支 `xiangze-zhu/work`）；PR 待本人账号 `trave1er999` 从 fork 发起，合并由 Yu 控制
- 对应F1/F2/F3/F4与支撑能力：F1 案例查询/来源/比较；F2 教学依据接口；F3 风险/费用/规则概念与案例解释；F4 可定位解释依据
- 完成的具体事情：见下表 XZ-01..07
- 修改文件和是否在允许范围：全部落在 `code_paths`（app/content.py、app/cases.py、tests/test_cases.py、tests/test_content.py）与 `document_paths`（content/cases、content/lessons、content/glossary、content/reviews、evidence/xiangze-zhu）及 `plan_path` 内；未改 `app/main.py`、`web/`、`.github/`、`scripts/`、`contracts/`
- 输入/输出与公共接口版本：目录版本 `qlab-cases-catalog-1.0.0`、`qlab-content-catalog-1.0.0`；路由 `/api/catalog/cases`、`/cases/{id}`、`/markets`、`/sources`、`/compare`、`/reviews`、`/lessons`、`/lessons/{id}`、`/glossary`、`/metadata`、`POST /validate/case`、`POST /validate`
- 真实运行的命令、测试结果和证据：`python -m pytest -q` → **155 passed, 10 subtests passed**（基线 111 + 本人 44）；证据见 `test-run.txt`
- 本次没有运行或未通过的检查：真实中美案例数据（无提交）；真实外部行情/数值接口（Yu 未实现）；真实 DeepSeek 调用（属 Tianqi）；真人测试
- 页面/资料/功能的复查步骤：`python -m pytest tests/test_cases.py tests/test_content.py -q`；或挂载 router 后 `curl localhost:8000/api/catalog/cases?market=CN`
- fixture、真实API、规则回答、真实模型各自的验证状态：合成 fixture=已测；原创教学内容=已测；真实API=未执行；真实模型=未执行
- 隐私/秘密/数据许可检查：未提交密钥、数据库、受限全文/切片/索引、无许可行情或个人日志；仅原创说明与合成 fixture
- 已知问题与需要其他人的内容：需 Yu 挂载 router 与批准 PLAN；需三人提交资料；需 Yu 提供 metrics 接口
- AI帮助及本人核查：AI 助手协助起草结构与测试；来源真实性、许可与“是否夸大”由本人按原始位置核对后才可标通过

## 任务状态

|任务|状态|证据|
|---|---|---|
|XZ-01 实际模块与接口范围|DONE|本 PLAN；源码核对结论 |
|XZ-02 案例结构与查询服务|DONE（实现）|app/cases.py；列表/详情/筛选/来源绑定测试|
|XZ-03 比较服务与不可比状态|DONE（实现）|比较负例测试（CURRENCY/PERIOD/SOURCE；UNKNOWN 不补值）|
|XZ-04 教学内容与术语服务|DONE|app/content.py；content/lessons、content/glossary；内容校验测试|
|XZ-05 材料复核与审核记录|BLOCKED|content/reviews/reviews.json 队列为 AWAITING_SUBMISSION；三人未提交|
|XZ-06 四项接入|IN_PROGRESS|路由与 mount(app) 已备；INTERFACE_REQUEST.md；站点内挂载待 Yu|
|XZ-07 测试、修复和完整交付|DONE|tests/test_cases.py、tests/test_content.py；全量 155 passed|

## R3补充核查

- 保留UI的基线、必要变更和截图位置：未改 UI；由 Zaixuan 在原比较页调用只读接口，无截图（本人不改前端）
- snapshot/plan/run/review如何对应：案例以 `case_id`/`version`/`source_id` 绑定；数值经 `metric_reference` 指向 Yu 的 snapshot；本模块不产生 run/review
- 本人执行的四项验收与实际状态：仅本人模块的接口级验证；F1 真实数据、F2/F4 真实 DeepSeek、跨模块同一 plan/run 的端到端复核未由本人执行
- F2是否在运行前、F4是否针对运行后：本人只提供依据接口，不生成 AI 文本，不改 F2/F4 时序
- 四项整体没有通过时不得写“产品全部完成”：同意；本记录不代表全站 F1—F4 通过

## 文件清单（本次提交）

- `app/content.py`（改）：教学内容目录与校验；向后兼容 `LESSONS`/`GLOSSARY`
- `app/cases.py`（新）：案例结构/查询/比较/校验服务与路由
- `tests/test_cases.py`（新）、`tests/test_content.py`（新）
- `content/cases/cases.json`、`sources.json`（新）；`content/lessons/lessons.json`、`content/glossary/glossary.json`、`content/reviews/reviews.json`（新）
- `content/{cases,lessons,glossary,reviews}/README.md`（改，记录格式）
- `plans/xiangze-zhu/PLAN.md`（改）
- `evidence/xiangze-zhu/{README.md,DELIVERY.md,INTERFACE_REQUEST.md,test-run.txt}`

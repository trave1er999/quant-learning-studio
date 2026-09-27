> Xingze.Zhu 的开发计划，关联任务 [#4](https://github.com/suiyisuixing/quant-learning-studio/issues/4)。本文件是本人 PLAN，不是已完成记录；实施范围须由 Yu 按 ACCESS_MODEL 的精确 PLAN blob 批准后生效。

# 我的开发计划｜R3（仅四名开发者填写）

- 显示名：Xingze.Zhu（历史别名 Xiangze.Zhu，同一人）
- GitHub login / URL：trave1er999 · https://github.com/trave1er999
- GitHub用户ID：243565339（TEAM_ROSTER 已登记；本人参与确认仍待回复）
- 对应任务/角色：开发 · 案例与教学内容模块（中美案例、来源、市场差异；结构与查询/比较/校验/测试）
- upstream仓库URL：https://github.com/suiyisuixing/quant-learning-studio
- 本人fork URL、分支：fork 待本人账号创建；本次工作在任务分支 `xiangze-zhu/work`
- 读取的基线commit：`main` 57cf025d0a06aff2a936b628b784c8d4975e368f；源码基线 `bootstrap/r3-collaboration` d9082869be5714b09e2587107359f4acc91426d1（PR #20，尚未合并入 main）
- 本机系统与实际运行状态：Linux + Python 3.10 venv；`python -m pytest` 全量 155 passed（含本人新增 44 项）

## 1. 我负责什么、不负责什么

负责：中美金融案例的数据结构、查询（列表/详情/市场筛选）、版本与来源绑定、比较服务与不可比口径说明、教学内容目录（术语/案例解释/学习目录）的读取筛选校验、输入校验、三人资料复核与入库前审核记录、四项功能中的内容/来源接入依据、本模块测试与修复。

不负责（按 MODULE_BOUNDARIES）：全站视觉与公共导航（Zaixuan）、账户与全局数据库迁移（Zaixuan）、DeepSeek 运行时与学生作答/进度/报告（Tianqi）、市场数据清洗与收益/风险/费用数值计算（Yu）、公共入口 `app/main.py`、CI/权限/依赖锁（Yu）。金融数值一律调用 Yu 的接口，不自行计算。

## 2. 当前实际情况

已存在并看过的代码/资料：`app/content.py`（原有 LESSONS/GLOSSARY）；`app/main.py` 中的 `/api/cases`（用户个人案例记录）与 `/api/lessons`；`app/engine.py`（Yu 的确定性引擎，收益/风险/费用的唯一来源）；`web/app.js` 的原比较页与资料页；`docs/INTERFACES.md`、`docs/MODULE_BOUNDARIES.md`、`docs/FOUR_FEATURES.md`、`.github/team-policy.json`、`tests/test_product.py`。

已运行的命令和结果：`python -m pytest -q` → 基线 111 passed；实现本人模块后 155 passed（真实执行，非旧记录）。

未运行/无法访问的部分：真实中美私募案例原始资料（后三人尚未提交，`research/submissions/*` 仅有 README）；Yu 的 `market_snapshot/metrics` 接口（未实现，记为外部依赖）；DeepSeek 真实模型调用（属 Tianqi，本人不调用）。

## R3四项职责映射

|功能|我主责/支持/测试什么|依赖谁|交付什么|怎样验证|当前真实状态|
|---|---|---|---|---|---|
|F1 市场数据的显示|中/美案例查询、市场筛选、来源与限制、可比性口径|Yu 的 snapshot/metrics；Zaixuan 页面|`app/cases.py` 案例目录与比较服务、路由|单元+HTTP 测试；市场筛选、来源缺失、不可比|DONE（fixture 级；真实案例待资料）|
|F2 人工智能的策划和分析|提供经审核的案例/教学内容与版本作为依据|Tianqi 检索/DeepSeek；Yu 参数校验|内容目录/术语读取接口 + 版本/来源校验|内容校验测试、未审核内容拒绝|DONE（接口级；DeepSeek 接入待 Tianqi）|
|F3 模拟经营的沙盘演练|提供风险/费用/规则的概念与案例解释依据|Yu 数值；Zaixuan 交互|术语与解释接口（数值引用 Yu）|术语查询测试、数值不自行计算|DONE（概念接口）|
|F4 最后的人工智能分析问题与复盘|提供可定位的概念/案例解释与来源|Tianqi 复盘；Yu 指标|带 `source_id`/版本的只读解释接口|来源绑定与权限测试|DONE（解释依据接口）|

不负责的项不由本人实现；本表状态仅代表本人模块，不代表全站 F1—F4 通过。

## 3. 我的完整任务清单（按依赖顺序）

|步骤|具体工作|预计交付|需要谁提供什么|拟修改路径|怎样验证|依赖/阻塞|
|---|---|---|---|---|---|---|
|XZ-01|核对 `app/content.py`、现有 Case/cases 行为；确认字段/输入输出/精确路径与完整计划|本 PLAN|Yu 冻结最小接口与精确路径|plans/xiangze-zhu/PLAN.md|计划与实际源码路径一致|无（已完成核对）|
|XZ-02|实现中美案例结构、列表/详情/市场筛选、版本与来源绑定，区分真实/教学/合成|app/cases.py + content/cases/*.json|真实案例资料由后三人提交|app/cases.py、content/cases/|列表/详情/筛选/来源绑定测试|真实案例数据 BLOCKED|
|XZ-03|比较服务：可比字段、UNKNOWN、不可比原因；数值引用 Yu|比较函数与负例|Yu 的 metrics 接口|app/cases.py|币种/期间/来源不匹配负例测试|数值计算依赖 Yu（EXTERNAL）|
|XZ-04|教学内容目录：术语/案例解释/学习目录读取筛选版本来源校验|app/content.py + content/lessons、content/glossary|无|app/content.py、content/lessons、content/glossary|内容校验与公开视图测试|由 Tianqi 接学习流程|
|XZ-05|接收三人资料卡，查原文定位/用途/许可/可得时间，记录退回原因|content/reviews/reviews.json + 审核记录|后三人提交资料|content/reviews/、evidence/xiangze-zhu/|复核记录校验测试；队列状态|BLOCKED：三人尚未提交|
|XZ-06|四项接入：F1 来源/比较；F2 当时依据；F3 风险费用概念；F4 解释依据|可调用服务+接入说明|Zaixuan 页面、Tianqi 上下文、Yu snapshot|app/cases.py、app/content.py、evidence/xiangze-zhu/INTERFACE_REQUEST.md|HTTP 路由测试 + 接口请求单|页面/上下文未就绪，接口已备|
|XZ-07|测试查询/比较/非法/重复/未知/未审核/无权限；修本模块 bug|tests/test_cases.py、tests/test_content.py|无|tests/|pytest 真实执行|无|

## 4. 输入与输出

需要的资料、接口、字段：三人的案例/论文资料卡（含原文定位、许可、可得时间）；Yu 的 `market_snapshot.metrics`（字段：`snapshot_id`、`instrument`、`market`、`currency`、`period`、`metric`、`value`、`version`）；Zaixuan 原比较页的数据展示挂点。

我提供的内容、接口、样例和版本：只读目录接口 `/api/catalog/cases`、`/cases/{case_id}`、`/markets`、`/sources`、`/compare`、`/reviews`、`/lessons`、`/lessons/{id}`、`/glossary`、`/metadata`、`POST /validate/case`、`POST /validate`；目录版本 `qlab-cases-catalog-1.0.0`、`qlab-content-catalog-1.0.0`；字段见各 JSON 的 schema。

缺失输入如何处理：缺真实案例时保留 `UNREVIEWED` 占位并返回 `UNKNOWN`，不补数字、不假装通过；缺 Yu 数值时比较结果只给口径与不可比原因，并显式标注 `EXTERNAL_NOT_IMPLEMENTED`。

## 5. 质量与公开范围

数值/引用/内容或操作如何核对：数值只引用 Yu 引擎；内容来自 `content/` 并做结构/版本/来源/重复校验；`approved=true` 等客户端字段被丢弃，审核状态只能服务端设定。正常与错误情况测试：列表/详情/筛选/比较/合法/非法/重复/未知/未审核/无权限均有测试。只保存在受控环境、绝不上传：任何未获许可的案例全文、受限论文原件、密钥与个人数据；公开仓库只放原创说明、合成 fixture 与元数据。

## 6. 风险与需要组长决定的事项

- 真实中美案例资料尚未到位，真实案例验收与 XZ-05 审核无法完成（不靠 AI 补造）。
- Yu 的 metrics 接口未定稿，比较服务暂无法返回真实数值，只返回口径与不可比原因。
- `app/main.py` 为 owner-only，需 Yu 挂载本人 router 才能进入现有站点；本人提供 `mount(app)` 与接口请求单，不擅自改共享入口。
- 需 Yu 按 ACCESS_MODEL 批准本 PLAN 的 blob SHA 与精确路径后，实施 PR 才符合 scope 门禁。

## UI和前后连接

是否需要改页面：不改。保留已认可 UI 与公共导航，仅由 Zaixuan 在原比较页/资料页调用只读目录接口，必要时新增“选择案例/查看来源限制/不可比提示”控件。输入来自 F1 的 market 选择与后三人资料；输出按 `source_id`/`version` 传给 Tianqi 的策划/复盘上下文与 Zaixuan 的展示。计划批准版本、模拟操作与报告各自持有独立版本，通过 `case_id`/`version`/`source_id` 关联，不共用一套身份。

## 7. 完成条件

可由另一人复查：`python -m pytest tests/test_cases.py tests/test_content.py` 全绿；全量 `python -m pytest` 不回归；`GET /api/catalog/*` 覆盖市场筛选、详情、来源缺失 403/404、币种/期间不可比；非法/重复/未知/未审核/无权限用例齐全；`content/` 内容可通过 `validate_catalog`/`validate_cases`/`validate_reviews`；真实案例以独立记录验收，不与 fixture 混算。

## 8. 交付更新

PR及commit：分支 `xiangze-zhu/work`（基于 `bootstrap/r3-collaboration` d908286）；提交见 git log 与 `evidence/xiangze-zhu/DELIVERY.md`（本人无上游写权，推送/PR 由本人账号 `trave1er999` 发起，合并由 Yu 控制）。

实际已完成：XZ-01/02/03/04/06/07 的代码、内容、路由与测试；XZ-07 全量 155 passed。

实际未完成：XZ-05 真实三人资料复核（BLOCKED：无提交）；真实中美案例数据与真实数值比较（BLOCKED：资料/接口待提供）；站点内挂载（待 Yu 合入 `mount(app)`）。

测试与复测：见 `evidence/xiangze-zhu/test-run.txt` 与 DELIVERY 记录，绑定本次 commit。

AI帮助做了什么、我核对或修改了什么：AI 助手协助起草结构与测试；Xiangze 需按本人真实判断核对来源、许可与是否夸大，并把未执行项如实标为 BLOCKED，不勾选未完成内容。

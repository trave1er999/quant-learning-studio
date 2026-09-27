# Xiangze.Zhu 的实际证据

仅在本人获准范围与真实执行后记录。每份记录区分源码、fixture、真实 API、HTTP 和真人验证。

- `DELIVERY.md`：本次交付记录（任务状态、改动文件、输入输出、真实测试、未完成项）。
- `INTERFACE_REQUEST.md`：给 Yu/Zaixuan/Tianqi 与三位资料成员的接入请求。
- `test-run.txt`：本次 `python -m pytest` 的真实输出（绑定本次 commit）。
- `http-smoke.txt`：`uvicorn` 真实进程 + `curl` 的 HTTP 冒烟结果（进程外，非 TestClient）。

本轮证据性质：源码级单元测试 + `TestClient` 进程内 HTTP + `uvicorn` 进程外真实 HTTP 路由验证，数据为明确标注的合成 fixture 与原创教学说明。**不含**真实中美私募基金案例、真实外部行情 HTTP、真实 DeepSeek 模型调用与真人测试；这些未执行，不在此声明为已完成。

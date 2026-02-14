# INKSTONE-AI

基于隐喻模型的汉英机器翻译文采度评价研究工程实现。

## 环境

- Python >= 3.10

## 一键运行

```bash
python scripts/bootstrap.py && python -m src.pipeline.run_all --config configs/systems.yaml
```

## 多供应商 LLM（本地 + 云端）

项目采用 OpenAI 兼容接口，可同时支持：

- 本地 LM Studio（如 Qwen3 8B）
- 云端 API（如 Kimi/OpenAI 兼容服务）

如需启用云端接口，请设置：

- `OPENAI_API_KEY`（或兼容 OpenAI API 的本地/第三方网关）

可在 `configs/systems.yaml` 中配置：

- `base_url`
- `model`
- `api_key_env`
- `timeout`
- `max_retries`

## 主要产物

- `reports/`：实验日志、图表、总报告
- `docs/methodology/`：可直接复用到论文的方法文档

## 产物检查

运行完成后应看到：

- `reports/figures/fig1-fig4` 的 `png+pdf`
- `reports/logs/experiment_log.md`
- `reports/report.md`
- `docs/methodology/*.md`

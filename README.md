# INKSTONE-AI

基于隐喻模型的汉英机器翻译文采度评价研究工程实现。

## 环境

- Python >= 3.10

## 一键运行

```bash
python scripts/bootstrap.py && python -m src.pipeline.run_all --config configs/systems.yaml
```

如果启用 LLM 评审或翻译，请设置：

- `OPENAI_API_KEY`（或兼容 OpenAI API 的本地/第三方网关）

## 主要产物

- `reports/`：实验日志、图表、总报告
- `docs/methodology/`：可直接复用到论文的方法文档

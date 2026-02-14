# INKSTONE-AI

基于隐喻模型的汉英机器翻译文采度评价研究工程实现。

## 环境

- Python >= 3.10

## 一键运行

```bash
python scripts/bootstrap.py && python -m src.pipeline.run_all --config configs/systems.yaml
```

## 可视化 GUI 面板

安装依赖后可启动可视化仪表盘（Streamlit）：

```bash
streamlit run src/gui/app.py
```

或使用脚本：

```bash
python scripts/run_gui.py
```

GUI 功能：

- 一键触发全流程运行
- 查看人模相关性与系统五维均值
- 查看数据质量（来源分布、去重统计、冻结清单）
- 预览 Fig1-Fig4 图表
- 浏览评测集/翻译样本
- 查看实验日志与方法文档存在性

详细说明见：`docs/GUI_GUIDE.md`

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
- `reports/run_manifest.jsonl`
- `docs/methodology/*.md`
- `data/processed/data_quality.jsonl`
- `data/processed/freeze_manifest.jsonl`

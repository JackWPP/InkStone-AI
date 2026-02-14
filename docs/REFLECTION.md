# 迭代反思（持续更新）

## 本轮推进摘要

1. 完成文档中文化主干改写（README、计划、论文清单、参考笔记、自动报告模板）。
2. 增加多供应商 LLM 适配层：支持 OpenAI 兼容接口、base_url、自定义 key env、重试。
3. 将翻译模块与标准评审模块接入 LLM 优先 + 回退机制。
4. 增强数据构建：去重、分层抽样、固定 seed、可选 books 管线。

## 新一轮推进（阶段0+阶段1）

1. 新增 `data_sources.py`：外部多格式解析（json/jsonl/csv/tsv/txt）+ 字段映射与隐喻类型归一。
2. `build_dataset.py` 重构：外部数据优先、books 补充、seed 兜底；输出 `data_quality.jsonl` 与 `freeze_manifest.jsonl`。
3. 新增 `baseline.py`：在流水线 start/end 自动写 `reports/run_manifest.jsonl`。
4. GUI 新增“数据质量”区块：展示去重统计、来源分布、隐喻类别分布、冻结清单。

## 当前问题

1. 外部数据集（CMDAG/CMC）仍需做“字段级解析器”而非通用 fallback。
2. Persona 评分仍存在回退路径，真实 LLM 质量受模型可用性影响。
3. 统计显著性与 bootstrap 置信区间尚未完全接入最终报告。

> 注：问题1已进入可执行版本（通用解析器 + 映射），下一步应补充仓库真实样例上的专用 parser 规则。

## 下一轮动作

1. 为 CMDAG/CMC 增加专用读取器与字段映射，减少脏数据分支。
2. 增强 ICL 采样策略：按隐喻类别分层抽取 few-shot。
3. 补齐 CI/显著性输出并写入 `experiment_log.md`。
4. 增加更多单元测试（schema、采样、评审输出格式）。

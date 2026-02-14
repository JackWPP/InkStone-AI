# SPEC v2.0.1 (Agent-Executable Thesis-Ready)

项目名称：《基于隐喻模型的汉英机器翻译文采度评价研究》 
repo名称：INKSTONE-AI
定位：首席架构师兼学术助理（工程闭环 + 论文素材自动产出）  
适用范围：**论文内部实验**（不对外发布原句全文与原始文本库）

> 本版本强调“拿到 SPEC 就能干活”：Agent 实现后，你只需配置 API Key（如使用 LLM），然后一条命令跑完整流水线，所有图/表/文档自动落盘。


> 关于LLM 请你支持多种供应商 我打算使用本地部署（LM Studio提供的Qwen3 8b模型以及API接入的kimi等模型混合的工作流 具体定不下来 所以请支持多种）
---

## 0. 一键运行与最小用户操作

### 0.1 One-command Quickstart（目标体验）
最终交付仓库必须支持：

1)（可选）设置环境变量：
- `OPENAI_API_KEY`（或你实际使用的 LLM Provider Key）

2) 一条命令跑完所有内容：

```bash
python -m src.pipeline.run_all --config configs/systems.yaml
```

运行结束后，必须在以下路径看到产物（详见第 12 章）：
- `reports/figures/*.png` + `reports/figures/*.pdf`
- `reports/logs/experiment_log.md`
- `docs/methodology/*.md`
- `reports/report.md`

### 0.2 “零人工数据准备”策略（强制）
为满足“你基本不需要做什么”，数据构建默认不依赖你提供《边城》文本；默认采用**可自动下载**的数据集（CMDAG/CMC）生成评测集。

同时保留“名著文本抽取”作为可选扩展：如果 `data/raw/books/*.txt` 存在，就同时跑名著抽取管线，并把来源写入方法文档；否则自动退化到公开隐喻数据集路线。

---

## 1. 研究问题与论文假设（Thesis-ready）

### 1.1 研究问题
传统 MT 自动评价指标（BLEU/METEOR）主要刻画词面与语义覆盖，对文学翻译中的“文采（雅）”与修辞效果敏感度不足。隐喻翻译涉及意象迁移、情感色彩、修辞对等与文化负载，因此适合作为文采度评价研究场景。

### 1.2 研究假设
- H1：不同翻译系统在文采五维上存在稳定差异。
- H2：文采五维与 BLEU/METEOR 的相关性有限，体现独立增益。
- H3：模拟人工 Persona 的伪 Gold 与标准评审模型输出正相关，说明评价框架一致性与可解释性成立。

---

## 2. 范围与非范围

### 2.1 范围（V2.0.1 必做）
- 数据构建：自动下载数据集并抽取固定评测集（默认 N=300）。
- 翻译系统：至少 A/B/C 三系统生成译文（2 个开源 NMT + 1 个 LLM 翻译）。
- 模拟人工（Persona）与标准评审（Model Judge），并实现 ICL few-shot 注入。
- 全过程日志与方法文档自动生成。
- 自动生成四张论文插图（PNG+PDF）：Fig1–Fig4。

### 2.2 非范围
- 不做真实人工标注。
- 不对外发布数据全文。
- 不做大规模 fine-tuning（用 ICL 替代）。

---

## 3. 数据构建（必须可自动下载 + 可复现）

### 3.1 默认数据源（Agent 必须能自动下载）
优先级：
1) CMDAG（推荐）
2) CMC（补充）

Agent 实现时必须提供**下载脚本**（见第 9.2），支持以下两种获取方式（至少一种可用）：
- 方式 A：`git clone` GitHub 仓库
- 方式 B：HuggingFace datasets API（作为网络受限/clone 失败备援）

### 3.2 数据标准化与字段（统一 Schema）
生成 `data/processed/source_items.jsonl`，每行字段：
- `sid`：稳定 ID（hash(text_norm + source + local_id)）
- `text_zh`
- `source_meta`：`{source, local_id, doc?, split?, license_tag}`
- `metaphor_meta`：`{metaphor_type, cultural_load, source_domain?, target_domain?}`（若数据集不提供则后续由 tagger 生成）
- `meta`：`{len_char, created_at}`

### 3.3 隐喻类别（用于 Fig1）
统一枚举（最终写入 `metaphor_meta.metaphor_type`）：
1) `simile`
2) `implicit`
3) `personification`
4) `synesthesia`
5) `cultural_allusion`
6) `dead_conventional`
7) `mixed_other`

若原数据集没有该字段，则由 `metaphor_tagger`（LLM）在评测集构建阶段补全。

### 3.4 评测集抽样与冻结（必须可复现）
- 目标：`N=300`
- 长度：12–60 字优先
- 去重：归一化后 hash 去重
- 分层：按 `metaphor_type` 分层，每类至少 `min(20, available)`
- 固定随机种子：`seed=20260215`

输出：
- `data/processed/eval_set.jsonl`（冻结；用于后续全部流程）
- `data/processed/pool.jsonl`（剩余候选）

### 3.5 可选：名著文本抽取（无需但支持）
若存在 `data/raw/books/*.txt`：
- 切句 → 规则粗筛 → `metaphor_tagger` 判定 → 合并进 `source_items.jsonl`（但 eval_set 抽样时仍以可复现规则为准）。
- 方法文档 `01_data_construction.md` 必须自动写明：本次 run 是否启用了 books 管线、使用了哪些书名文件（内部）。

---

## 4. 翻译系统 A/B/C（可复现 + 可断点）

### 4.1 系统定义（必须至少三套）
- System A：开源 NMT（HF 模型）
- System B：更强开源 NMT（HF 模型）
- System C：LLM 翻译（API/本地模型均可；V1 默认 API）

### 4.2 翻译输出与缓存
- 输出：`data/processed/translations.jsonl`
- 缓存必须实现（sqlite），key：`(sid, system_id, prompt_version)`
- 断点续跑：重复执行 `translate` 不得重新请求已缓存项。

---

## 5. 文采五维指标与数学定义（Thesis-ready）

五维（1–5 整数）：
- IF（Imagery Fidelity）
- EC（Emotional Congruence）
- RE（Rhetorical Equivalence）
- CA（Cultural Adaptability）
- LE（Linguistic Elegance）

综合分：
- `OV = round(w · s)`
- 默认权重：`w = [0.25, 0.20, 0.25, 0.15, 0.15]`

系统级统计：均值、标准差、（可选）bootstrap 95% CI。

---

## 6. 模拟人工 Persona + ICL 替代微调（必须可跑）

### 6.1 新增模块（强制）
- `src/pipeline/judge_persona.py`：3 Persona 生成伪人工评分
- `src/pipeline/judge_standard.py`：标准评审输出模型评分（支持 ICL）
- `src/pipeline/icl_builder.py`：构建 few-shot bank（推荐）

### 6.2 Persona 设定（必须写入 prompts 并固化版本）
- P1 Professor：严苛、重忠实与修辞对等
- P2 Writer：重语言优雅与意象
- P3 Reader：重可读性与直观理解

每个 Persona 必须输出结构化 JSON：五维 + OV + 每维 evidence + rationale。

### 6.3 伪 Gold 聚合规则
对每条 `(sid, system_id)`：
- 取 3 Persona 的五维分数 median 得到 `scores_gold`
- `OV_gold = round(w · s_gold)`
- 记录分歧：每维 range（max-min）

输出：`data/processed/persona_gold.jsonl`

### 6.4 ICL Few-shot 注入（替代 fine-tuning）
- 从 `persona_gold.jsonl` 中选择高质量样本：`OV_gold >= 4` 且 max range <= 1
- 形成 `data/processed/few_shot_bank.jsonl`（含中文、译文、gold 分数、gold 理由）
- `judge_standard` 在评审时注入 K=3–5 条示例（固定 seed，并按隐喻类别分层采样）

输出：`data/processed/judge_scores.jsonl`

---

## 7. 全过程文档化（Documentation-First，自动生成可复制进论文）

### 7.1 实验日志 experiment_log.md（强制）
路径：`reports/logs/experiment_log.md`

必须包含：
- Run ID（时间戳 + short hash）
- Git commit hash（可选）
- 数据来源摘要（CMDAG/CMC/books），N、seed、隐喻类别分布
- 翻译系统配置（模型名/版本/温度/prompt_version）
- Persona 配置与 prompt_version
- ICL 配置：K、seed、few-shot bank 统计
- 结果摘要：
  - 系统 A/B/C 五维均值与 OV 均值
  - Persona Gold vs Standard Judge 的相关性（Fig2 的数字）
  - 文采维度 vs BLEU/METEOR 相关性摘要（Fig4 的数字）
- 产物索引：所有 figures 与 report 路径

建议格式：顶部 YAML front-matter + 下方 Markdown 表格。

### 7.2 方法论文档（强制自动生成）
目录：`docs/methodology/`

必须生成三份 Markdown（内容可直接复制到论文）：

1) `01_data_construction.md`
- 默认路线：从 CMDAG/CMC 构建评测集的完整流程
- 可选路线：从 books（如《边城》）抽取句子的流程（若本次 run 未启用也必须说明“未启用”）
- 必须包含：`metaphor_tagger` 的完整 prompt（从 `configs/prompts/metaphor_tagger_v1.txt` 读取并嵌入）

2) `02_annotation_guidelines.md`
- 3 Persona 设定、偏好、评分风格
- 五维评分标准（1–5）与触发式降分规则
- Persona 聚合 Gold 的规则
- 必须嵌入 Persona prompts（从 `configs/prompts/persona_*.txt` 读取）

3) `03_metric_definition.md`
- 五维定义与 OV 公式
- 系统级统计定义、置信区间计算（若启用）
- 与传统指标相关性分析定义（Spearman）

---

## 8. 自动化“论文插图”工厂（必须生成 PNG+PDF）

### 8.1 新增模块（强制）
- `src/pipeline/visualization.py`

### 8.2 输出规则（强制）
- 输出目录：`reports/figures/`
- 每张图输出：
  - `*.png`（≥300 DPI）
  - `*.pdf`（矢量）

### 8.3 必须生成的四张图

Fig 1. Data Distribution（饼图）
- 输入：`eval_set.jsonl` 的 `metaphor_type`
- 输出：
  - `reports/figures/fig1_data_distribution.png`
  - `reports/figures/fig1_data_distribution.pdf`

Fig 2. Human-Model Correlation（散点 + 回归）
- x：`OV_gold`（Persona 聚合）
- y：`OV_model`（judge_standard）
- 必须标注 Pearson r 和 Spearman ρ（至少一个）
- 输出：
  - `reports/figures/fig2_human_model_correlation.png`
  - `reports/figures/fig2_human_model_correlation.pdf`

Fig 3. Radar Chart（五维雷达对比）
- 输入：系统 A/B/C 的五维均值 `[IF, EC, RE, CA, LE]`
- 输出：
  - `reports/figures/fig3_radar_system_comparison.png`
  - `reports/figures/fig3_radar_system_comparison.pdf`

Fig 4. Heatmap（相关性热力图）
- 相关性矩阵：文采五维（句级）× 传统指标（句级 BLEU/METEOR）
- 默认相关系数：Spearman
- 输出：
  - `reports/figures/fig4_metric_correlation_heatmap.png`
  - `reports/figures/fig4_metric_correlation_heatmap.pdf`

### 8.4 可视化技术栈与样式
- 必须使用 `matplotlib`（允许启用 style：`seaborn-v0_8`）
- 字号默认：标题 14–16，轴标签 12，刻度 10（可在 `configs/viz.yaml` 配置）
- 雷达图必须统一尺度 1–5。

---

## 9. “Agent 拿到就能干活”的实现约束（关键）

### 9.1 Repo 必须包含的脚本（强制）
为确保“你几乎不需要做什么”，Agent 最终交付必须包含以下脚本，并在 README 中给出一条命令。

1) `scripts/bootstrap.py`
- 创建/检查 Python 环境
- 安装依赖（`pip install -r requirements.txt`）
- 下载必要 NLTK 资源（METEOR 需要 wordnet 等）
- 下载数据集（调用 `scripts/download_datasets.py`）
- 生成默认配置文件（若不存在）：`configs/systems.yaml`

2) `scripts/download_datasets.py`
- 自动获取 CMDAG/CMC（GitHub clone 或 HF datasets 备援）
- 下载后做完整性检查：文件存在、样本数 > 最小阈值

3) `scripts/preflight.py`
- 检查：
  - Python 版本（>=3.10）
  - 依赖可 import
  - 若启用 LLM：API key 是否存在
  - 输出目录可写
- 失败时给出“可执行的修复指令”

4) `scripts/run_all.py`（可选，但推荐）
- 包装 `python -m src.pipeline.run_all ...`，自动串联 bootstrap + run_all

### 9.2 网络与下载失败的备援策略（强制）
- GitHub clone 失败 → 自动走 HF datasets
- HF 失败 → 给出清晰错误并退出（不得 silent fail）
- Transformers 模型下载失败 → 提示 `HF_HOME`/镜像设置建议（写入 README）

---

## 10. 工程结构（最终交付必须一致）

```
mt_grace_eval/
  README.md
  requirements.txt
  pyproject.toml
  configs/
    systems.yaml
    viz.yaml
    prompts/
      trans_v1.txt
      metaphor_tagger_v1.txt
      persona_professor_v1.txt
      persona_writer_v1.txt
      persona_reader_v1.txt
      judge_standard_v1.txt
      judge_standard_v1_icl.txt
  scripts/
    bootstrap.py
    download_datasets.py
    preflight.py
    run_all.py
  docs/
    methodology/
      01_data_construction.md           # 自动生成
      02_annotation_guidelines.md       # 自动生成
      03_metric_definition.md           # 自动生成
  data/
    raw/
      books/                            # 可选：你放名著 txt
    external/                           # 自动下载/clone（不提交）
    processed/
      source_items.jsonl
      pool.jsonl
      eval_set.jsonl
      translations.jsonl
      persona_gold.jsonl
      few_shot_bank.jsonl
      judge_scores.jsonl
      metrics_traditional.jsonl
  reports/
    figures/
    logs/
      experiment_log.md
    report.md
  src/
    core/
      schema.py
      io.py
      normalize.py
      cache.py
      metrics_traditional.py
    pipeline/
      run_all.py
      build_dataset.py
      translate.py
      judge_persona.py
      icl_builder.py
      judge_standard.py
      metrics.py
      visualization.py
      report.py
  tests/
```

---

## 11. 传统指标（BLEU/METEOR）与 reference 策略（必须可跑）

### 11.1 句级 BLEU
- 使用 `sacrebleu` 的 sentence-level BLEU（或 corpus-level + 句级分解）

### 11.2 METEOR
- 使用 `nltk.translate.meteor_score`
- `scripts/bootstrap.py` 必须自动下载 `wordnet` 等 NLTK 资源

### 11.3 reference 译文（内部实验的“伪参考”）
默认选择（必须在 log 中记录）：
- Option R1（默认）：使用 Persona Writer 生成的 reference（更“学术”）
- Option R2：System C（LLM 翻译）作为 reference（更省成本，但有偏差）

实现要求：
- `metrics_traditional.py` 必须支持两种 reference_source，并把选择写入 `metrics_traditional.jsonl.reference_source`。

---

## 12. 输出产物（强制路径清单：MD + PNG/PDF）

### 12.1 自动生成文档（Markdown）
- `docs/methodology/01_data_construction.md`
- `docs/methodology/02_annotation_guidelines.md`
- `docs/methodology/03_metric_definition.md`
- `reports/logs/experiment_log.md`
- `reports/report.md`

### 12.2 自动生成论文插图（PNG + PDF）
- `reports/figures/fig1_data_distribution.png`
- `reports/figures/fig1_data_distribution.pdf`
- `reports/figures/fig2_human_model_correlation.png`
- `reports/figures/fig2_human_model_correlation.pdf`
- `reports/figures/fig3_radar_system_comparison.png`
- `reports/figures/fig3_radar_system_comparison.pdf`
- `reports/figures/fig4_metric_correlation_heatmap.png`
- `reports/figures/fig4_metric_correlation_heatmap.pdf`

### 12.3 自动生成中间数据（内部实验）
- `data/processed/source_items.jsonl`
- `data/processed/pool.jsonl`
- `data/processed/eval_set.jsonl`
- `data/processed/translations.jsonl`
- `data/processed/persona_gold.jsonl`
- `data/processed/few_shot_bank.jsonl`
- `data/processed/judge_scores.jsonl`
- `data/processed/metrics_traditional.jsonl`

---

## 13. 验收标准（Agent 交付后，你只跑一条命令就能验收）

必须满足：
1) `scripts/bootstrap.py` 可在干净环境跑通（下载数据、安装依赖、准备资源）。
2) `python -m src.pipeline.run_all ...` 一次跑完，且所有第 12 章产物存在。
3) `experiment_log.md` 中包含 run 参数、系统配置、关键统计与图路径。
4) Fig1–Fig4 同时存在 PNG+PDF，分辨率与字体可读。
5) methodology 三份文档内容完整（含 prompts），可直接复制进论文。

---

## 14. README 必须包含的最短使用说明（Agent 必须写）

- 环境：Python>=3.10
- 一键运行：
  - `python scripts/bootstrap.py && python -m src.pipeline.run_all --config configs/systems.yaml`
- 若使用 LLM：提示设置 `OPENAI_API_KEY`
- 产物在哪里：直接列出 `reports/` 与 `docs/methodology/`。


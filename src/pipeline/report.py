from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.core.io import read_jsonl


def _render_methodology(config: dict[str, Any]) -> None:
    prompts_dir = Path(config["paths"]["prompts_dir"])
    mdir = Path(config["paths"]["methodology_dir"])
    mdir.mkdir(parents=True, exist_ok=True)

    tagger_prompt = (prompts_dir / "metaphor_tagger_v1.txt").read_text(encoding="utf-8")
    p_prof = (prompts_dir / "persona_professor_v1.txt").read_text(encoding="utf-8")
    p_writer = (prompts_dir / "persona_writer_v1.txt").read_text(encoding="utf-8")
    p_reader = (prompts_dir / "persona_reader_v1.txt").read_text(encoding="utf-8")

    (mdir / "01_data_construction.md").write_text(
        "# 数据构建\n\n"
        "本次流程优先解析外部数据（CMDAG/CMC 目录），并支持 books 可选补充，最后以 seed 样本兜底。\n\n"
        "## 隐喻标注提示词\n\n"
        "```text\n"
        f"{tagger_prompt}\n"
        "```\n",
        encoding="utf-8",
    )

    (mdir / "02_annotation_guidelines.md").write_text(
        "# 标注与评审准则\n\n"
        "## Persona 提示词\n\n"
        "### 教授 Persona\n\n"
        "```text\n"
        f"{p_prof}\n"
        "```\n\n"
        "### 作家 Persona\n\n"
        "```text\n"
        f"{p_writer}\n"
        "```\n\n"
        "### 读者 Persona\n\n"
        "```text\n"
        f"{p_reader}\n"
        "```\n",
        encoding="utf-8",
    )

    (mdir / "03_metric_definition.md").write_text(
        "# 指标定义\n\n"
        "五维：IF, EC, RE, CA, LE。\n\n"
        "OV = round(0.25*IF + 0.20*EC + 0.25*RE + 0.15*CA + 0.15*LE)。\n\n"
        "相关性分析默认 Spearman。\n",
        encoding="utf-8",
    )


def run(
    config: dict[str, Any], metrics_summary: dict[str, Any], viz_stats: dict[str, Any]
) -> dict[str, Any]:
    reports_dir = Path(config["paths"]["reports_dir"])
    logs_dir = reports_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    _render_methodology(config)

    source_rows = read_jsonl(
        Path(config["paths"]["data_processed"]) / "source_items.jsonl"
    )
    source_counter: dict[str, int] = {}
    for row in source_rows:
        src = str(row.get("source_meta", {}).get("source", "unknown"))
        source_counter[src] = source_counter.get(src, 0) + 1

    quality_rows = read_jsonl(
        Path(config["paths"]["data_processed"]) / "data_quality.jsonl"
    )
    quality = quality_rows[0] if quality_rows else {}
    parser_meta = quality.get("parser_meta", {}) if isinstance(quality, dict) else {}
    trans_stats_rows = read_jsonl(
        Path(config["paths"]["data_processed"]) / "translation_stats.jsonl"
    )
    trans_stats = trans_stats_rows[0] if trans_stats_rows else {}

    books_enabled = "books" in source_counter
    books_files = sorted(Path(config["paths"]["data_raw_books"]).glob("*.txt"))
    books_list = ", ".join(p.name for p in books_files) if books_files else "无"

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    log_path = logs_dir / "experiment_log.md"
    log_text = (
        "---\n"
        f"run_id: {run_id}\n"
        "seed: 20260215\n"
        "---\n\n"
        "# 实验日志\n\n"
        f"- 人模 Spearman 相关: {metrics_summary.get('human_model_spearman', 0.0):.4f}\n"
        f"- 人模 Spearman 95%CI: {metrics_summary.get('human_model_spearman_ci95', {})}\n"
        f"- Fig2 Pearson r: {viz_stats.get('pearson_r', 0.0):.4f}\n"
        f"- Fig2 Spearman rho: {viz_stats.get('spearman_rho', 0.0):.4f}\n"
        f"- 数据来源计数: {source_counter}\n"
        f"- 数据质量: rows_after_dedup={quality.get('rows_after_dedup', 0)}, duplicates_removed={quality.get('duplicates_removed', 0)}\n"
        f"- 外部解析文件数: {parser_meta.get('n_files', 0)}\n"
        f"- 翻译统计: cache_hit={trans_stats.get('cache_hit', 0)}, hf_success={trans_stats.get('hf_success', 0)}, hf_fail={trans_stats.get('hf_fail', 0)}, llm_success={trans_stats.get('llm_success', 0)}, fallback_mock={trans_stats.get('fallback_mock', 0)}\n"
        f"- books 管线启用: {'是' if books_enabled else '否'}\n"
        f"- books 文件: {books_list}\n"
        "- 图表产物: reports/figures/fig1-fig4 (png/pdf)\n"
    )
    log_path.write_text(log_text, encoding="utf-8")

    report_path = reports_dir / "report.md"
    eval_count = len(
        read_jsonl(Path(config["paths"]["data_processed"]) / "eval_set.jsonl")
    )
    report_path.write_text(
        "# INKSTONE-AI 实验报告\n\n"
        f"- 评测集规模: {eval_count}\n"
        f"- 人模 Spearman 相关: {metrics_summary.get('human_model_spearman', 0.0):.4f}\n"
        "- 主要产物已生成于 reports/figures 与 docs/methodology\n",
        encoding="utf-8",
    )
    return {"log": str(log_path), "report": str(report_path)}

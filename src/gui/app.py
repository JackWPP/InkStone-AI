from __future__ import annotations

from pathlib import Path
from typing import Any

import streamlit as st

from src.gui.dashboard import (
    load_dashboard_data,
    read_jsonl_safe,
    run_pipeline_subprocess,
)


ROOT = Path(__file__).resolve().parents[2]


def _show_file_hint(path: Path) -> None:
    if path.exists():
        st.success(f"已找到：{path}")
    else:
        st.warning(f"未找到：{path}（请先运行流水线）")


def _render_overview(data: dict[str, Any]) -> None:
    summary = data.get("summary", {})
    col1, col2 = st.columns(2)
    with col1:
        st.metric(
            "人模 Spearman 相关", f"{summary.get('human_model_spearman', 0.0):.4f}"
        )
    with col2:
        st.metric("系统数量", len(summary.get("system_means", {})))

    st.subheader("系统五维均值")
    means = summary.get("system_means", {})
    if means:
        table_rows = []
        for system_id, dims in means.items():
            row = {"system_id": system_id}
            row.update(dims)
            table_rows.append(row)
        st.dataframe(table_rows, use_container_width=True)
    else:
        st.info("暂无 metrics_summary 数据。")


def _render_quality(data: dict[str, Any]) -> None:
    st.subheader("数据质量")
    files = data.get("files", {})
    quality_path = files.get("data_quality")
    freeze_path = files.get("freeze_manifest")

    quality_rows = (
        read_jsonl_safe(quality_path) if isinstance(quality_path, Path) else []
    )
    quality = quality_rows[0] if quality_rows else {}

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("去重后样本数", int(quality.get("rows_after_dedup", 0)))
    with col2:
        st.metric("评测集样本数", int(quality.get("eval_rows", 0)))
    with col3:
        st.metric("去重删除数", int(quality.get("duplicates_removed", 0)))

    source_counts = quality.get("source_counts", {})
    if isinstance(source_counts, dict) and source_counts:
        st.markdown("**来源分布**")
        source_rows = [
            {"source": k, "count": int(v)} for k, v in sorted(source_counts.items())
        ]
        st.dataframe(source_rows, use_container_width=True)

    type_counts = quality.get("metaphor_type_counts", {})
    if isinstance(type_counts, dict) and type_counts:
        st.markdown("**隐喻类别分布**")
        type_rows = [
            {"metaphor_type": k, "count": int(v)}
            for k, v in sorted(type_counts.items())
        ]
        st.dataframe(type_rows, use_container_width=True)

    if isinstance(freeze_path, Path):
        freeze_rows = read_jsonl_safe(freeze_path)
        if freeze_rows:
            st.markdown("**冻结清单（最近一条）**")
            st.json(freeze_rows[-1])


def _render_figures(data: dict[str, Any]) -> None:
    st.subheader("论文图表预览")
    figures = data.get("figures", {})
    tabs = st.tabs(["Fig1", "Fig2", "Fig3", "Fig4"])
    keys = ["fig1", "fig2", "fig3", "fig4"]
    for tab, key in zip(tabs, keys):
        with tab:
            fp = figures.get(key)
            if isinstance(fp, Path) and fp.exists():
                st.image(str(fp), caption=fp.name, use_column_width=True)
                pdf = fp.with_suffix(".pdf")
                if pdf.exists():
                    pdf_bytes = pdf.read_bytes()
                    st.download_button(
                        label=f"下载 {pdf.name}",
                        data=pdf_bytes,
                        file_name=pdf.name,
                        mime="application/pdf",
                        key=f"dl_{key}",
                    )
            else:
                st.info(f"{key} 尚未生成。")


def _render_data_samples(data: dict[str, Any]) -> None:
    st.subheader("数据样本")
    files = data.get("files", {})
    eval_path = files.get("eval_set")
    trans_path = files.get("translations")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**评测集样本**")
        rows = read_jsonl_safe(eval_path)[:20] if isinstance(eval_path, Path) else []
        if rows:
            st.dataframe(rows, use_container_width=True)
        else:
            st.info("暂无评测集数据。")
    with col2:
        st.markdown("**翻译结果样本**")
        rows = read_jsonl_safe(trans_path)[:20] if isinstance(trans_path, Path) else []
        if rows:
            st.dataframe(rows, use_container_width=True)
        else:
            st.info("暂无翻译结果数据。")


def _render_reports(data: dict[str, Any]) -> None:
    st.subheader("日志与方法文档")
    files = data.get("files", {})
    entries = [
        ("实验日志", "experiment_log"),
        ("总报告", "report"),
        ("方法-数据构建", "method_data"),
        ("方法-标注准则", "method_anno"),
        ("方法-指标定义", "method_metric"),
    ]
    tabs = st.tabs([e[0] for e in entries])
    for tab, (title, key) in zip(tabs, entries):
        with tab:
            path = files.get(key)
            if not isinstance(path, Path):
                st.warning(f"{title} 路径未配置")
                continue
            _show_file_hint(path)
            if path.exists():
                text = path.read_text(encoding="utf-8", errors="ignore")
                st.markdown(text)


def main() -> None:
    st.set_page_config(page_title="INKSTONE-AI 可视化面板", layout="wide")
    st.title("INKSTONE-AI 可视化面板")
    st.caption("用于运行管线、查看核心指标、预览 Fig1-Fig4、浏览样本与文档。")

    with st.sidebar:
        st.header("运行控制")
        config_path = st.text_input("配置文件", value="configs/systems.yaml")
        enable_llm = st.toggle("启用真实 LLM 调用（可能较慢）", value=False)
        run_clicked = st.button("运行全流程")
        refresh_clicked = st.button("刷新面板")

    if run_clicked:
        with st.spinner("正在执行流水线，请稍候..."):
            code, out, err = run_pipeline_subprocess(
                ROOT, config_path=config_path, enable_llm=enable_llm
            )
        if code == 0:
            st.success("流水线执行完成")
        else:
            st.error(f"流水线执行失败，退出码={code}")
        if out.strip():
            st.text_area("标准输出", out, height=180)
        if err.strip():
            st.text_area("错误输出", err, height=180)

    if refresh_clicked:
        st.rerun()

    data = load_dashboard_data(ROOT)
    _render_overview(data)
    _render_quality(data)
    _render_figures(data)
    _render_data_samples(data)
    _render_reports(data)


if __name__ == "__main__":
    main()

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from src.core.io import read_jsonl, write_jsonl
from src.core.llm_client import chat_json, llm_config_from_dict
from src.core.schema import DIMENSIONS


PERSONAS = ["professor", "writer", "reader"]
WEIGHTS = [0.25, 0.2, 0.25, 0.15, 0.15]


def _score_seed(sid: str, system_id: str, persona: str) -> dict[str, int]:
    seed = sum(ord(c) for c in f"{sid}:{system_id}:{persona}")
    values: dict[str, int] = {}
    for i, dim in enumerate(DIMENSIONS):
        values[dim] = 1 + ((seed + i * 7) % 5)
    return values


def _ov(scores: dict[str, int]) -> int:
    ordered = [scores[d] for d in DIMENSIONS]
    return int(round(sum(w * s for w, s in zip(WEIGHTS, ordered))))


def _persona_prompt_file(name: str) -> str:
    return {
        "professor": "persona_professor_v1.txt",
        "writer": "persona_writer_v1.txt",
        "reader": "persona_reader_v1.txt",
    }[name]


def run(config: dict[str, Any]) -> dict[str, Any]:
    processed = Path(config["paths"]["data_processed"])
    prompts_dir = Path(config["paths"]["prompts_dir"])
    rows = read_jsonl(processed / "translations.jsonl")
    llm_cfg = llm_config_from_dict(config["judge"]["standard_model"])
    llm_enabled = os.getenv("INKSTONE_ENABLE_LLM", "0") == "1"

    out_rows: list[dict[str, Any]] = []
    for row in rows:
        sid = row["sid"]
        system_id = row["system_id"]
        persona_scores: list[dict[str, int]] = []
        persona_outputs: list[dict[str, Any]] = []
        for persona in PERSONAS:
            prompt_text = (prompts_dir / _persona_prompt_file(persona)).read_text(
                encoding="utf-8"
            )
            user_prompt = (
                f"中文原句：{row['text_zh']}\n"
                f"译文：{row['translation']}\n"
                "请返回 JSON 字段：scores（包含 IF/EC/RE/CA/LE）、OV、evidence、rationale。"
            )
            llm_json = (
                chat_json(
                    llm_cfg,
                    prompt_text,
                    user_prompt,
                    required_fields=["scores", "OV", "rationale"],
                )
                if llm_enabled
                else None
            )
            if llm_json is not None and isinstance(llm_json.get("scores"), dict):
                scores = {
                    dim: max(1, min(5, int(llm_json["scores"].get(dim, 3))))
                    for dim in DIMENSIONS
                }
                evidence = llm_json.get("evidence", {})
                rationale = str(llm_json.get("rationale", ""))
                mode = "llm"
            else:
                scores = _score_seed(sid, system_id, persona)
                evidence = {dim: "fallback_seed" for dim in DIMENSIONS}
                rationale = "使用确定性回退评分。"
                mode = "fallback_seed"

            persona_scores.append(scores)
            persona_outputs.append(
                {
                    "persona": persona,
                    "scores": scores,
                    "OV": _ov(scores),
                    "evidence": evidence,
                    "rationale": rationale,
                    "mode": mode,
                }
            )
        gold_scores: dict[str, int] = {}
        ranges: dict[str, int] = {}
        for dim in DIMENSIONS:
            vals = sorted(item[dim] for item in persona_scores)
            gold_scores[dim] = vals[1]
            ranges[dim] = vals[-1] - vals[0]
        out_rows.append(
            {
                "sid": sid,
                "system_id": system_id,
                "scores_gold": gold_scores,
                "OV_gold": _ov(gold_scores),
                "range": ranges,
                "persona_outputs": persona_outputs,
            }
        )

    out_path = processed / "persona_gold.jsonl"
    write_jsonl(out_path, out_rows)
    return {"rows": len(out_rows), "persona_gold": str(out_path)}


if __name__ == "__main__":
    from src.pipeline.config import load_config

    cfg = load_config("configs/systems.yaml")
    print(run(cfg))

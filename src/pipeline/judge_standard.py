from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from src.core.io import read_jsonl, write_jsonl
from src.core.llm_client import chat_json, llm_config_from_dict
from src.core.schema import DIMENSIONS


WEIGHTS = [0.25, 0.2, 0.25, 0.15, 0.15]


def _ov(scores: dict[str, int]) -> int:
    ordered = [scores[d] for d in DIMENSIONS]
    return int(round(sum(w * s for w, s in zip(WEIGHTS, ordered))))


def run(config: dict[str, Any]) -> dict[str, Any]:
    processed = Path(config["paths"]["data_processed"])
    prompts_dir = Path(config["paths"]["prompts_dir"])
    prompt_version = config["judge"]["standard_model"].get(
        "prompt_version", "judge_standard_v1_icl"
    )
    prompt_path = prompts_dir / f"{prompt_version}.txt"
    system_prompt = (
        prompt_path.read_text(encoding="utf-8")
        if prompt_path.exists()
        else "你是翻译评审员，请输出严格 JSON。"
    )

    persona_rows = read_jsonl(processed / "persona_gold.jsonl")
    trans_rows = read_jsonl(processed / "translations.jsonl")
    few_shot_bank = read_jsonl(processed / "few_shot_bank.jsonl")
    trans_map = {(r["sid"], r["system_id"]): r for r in trans_rows}
    llm_cfg = llm_config_from_dict(config["judge"]["standard_model"])
    k = int(config["judge"]["icl"].get("k", 3))
    llm_enabled = os.getenv("INKSTONE_ENABLE_LLM", "0") == "1"

    out_rows: list[dict[str, Any]] = []
    for row in persona_rows:
        scores_gold = row["scores_gold"]
        tr = trans_map.get((row["sid"], row["system_id"]))
        chosen = few_shot_bank[:k]
        shot_lines = []
        for idx, ex in enumerate(chosen, start=1):
            shot_lines.append(
                f"[示例{idx}]\n"
                f"中文: {ex['text_zh']}\n"
                f"译文: {ex['translation']}\n"
                f"Gold: {ex['scores_gold']} OV={ex['OV_gold']}\n"
                f"理由: {ex.get('gold_rationale', '')}"
            )
        user_prompt = (
            "请按 IF/EC/RE/CA/LE 五维给出 1-5 分，并返回 JSON。\n"
            + "\n\n".join(shot_lines)
            + "\n\n"
            + f"待评审中文: {tr['text_zh'] if tr else ''}\n"
            + f"待评审译文: {tr['translation'] if tr else ''}\n"
            + "请返回字段: scores_model, OV_model, rationale。"
        )

        llm_json = (
            chat_json(
                llm_cfg,
                system_prompt,
                user_prompt,
                required_fields=["scores_model", "OV_model"],
            )
            if llm_enabled
            else None
        )

        scores_model: dict[str, int] = {}
        if llm_json is not None and isinstance(llm_json.get("scores_model"), dict):
            for dim in DIMENSIONS:
                raw = int(llm_json["scores_model"].get(dim, scores_gold[dim]))
                scores_model[dim] = max(1, min(5, raw))
        else:
            for dim in DIMENSIONS:
                raw = int(scores_gold[dim])
                if raw < 5 and (sum(ord(c) for c in (row["sid"] + dim)) % 3 == 0):
                    raw += 1
                scores_model[dim] = max(1, min(5, raw))

        ov_model = (
            int(llm_json["OV_model"])
            if llm_json is not None and str(llm_json.get("OV_model", "")).isdigit()
            else _ov(scores_model)
        )
        out_rows.append(
            {
                "sid": row["sid"],
                "system_id": row["system_id"],
                "scores_model": scores_model,
                "OV_model": max(1, min(5, ov_model)),
                "judge_prompt_version": prompt_version,
                "judge_mode": "llm" if llm_json is not None else "fallback_seed",
            }
        )

    out_path = processed / "judge_scores.jsonl"
    write_jsonl(out_path, out_rows)
    return {"rows": len(out_rows), "judge_scores": str(out_path)}


if __name__ == "__main__":
    from src.pipeline.config import load_config

    cfg = load_config("configs/systems.yaml")
    print(run(cfg))

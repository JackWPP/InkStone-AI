from __future__ import annotations

import importlib
from typing import Any


def sentence_bleu(reference: str, hypothesis: str) -> float:
    try:
        sacrebleu_mod = importlib.import_module("sacrebleu")
        sentence_bleu_fn = getattr(sacrebleu_mod, "sentence_bleu")
        score_obj = sentence_bleu_fn(hypothesis, [reference])
        return float(score_obj.score)
    except Exception:
        ref_tokens = reference.split()
        hyp_tokens = hypothesis.split()
        if not ref_tokens or not hyp_tokens:
            return 0.0
        overlap = len(set(ref_tokens) & set(hyp_tokens))
        precision = overlap / max(1, len(hyp_tokens))
        return round(precision * 100.0, 4)


def sentence_meteor(reference: str, hypothesis: str) -> float:
    try:
        meteor_mod = importlib.import_module("nltk.translate.meteor_score")
        meteor_score_fn = getattr(meteor_mod, "meteor_score")
        ref_tokens = reference.split()
        hyp_tokens = hypothesis.split()
        return float(meteor_score_fn([ref_tokens], hyp_tokens))
    except Exception:
        ref_tokens = reference.split()
        hyp_tokens = hypothesis.split()
        if not ref_tokens or not hyp_tokens:
            return 0.0
        overlap = len(set(ref_tokens) & set(hyp_tokens))
        recall = overlap / max(1, len(ref_tokens))
        precision = overlap / max(1, len(hyp_tokens))
        if recall + precision == 0:
            return 0.0
        return (10 * precision * recall) / (recall + 9 * precision)


def compute_traditional_row(
    reference: str, hypothesis: str, reference_source: str
) -> dict[str, Any]:
    return {
        "bleu": sentence_bleu(reference, hypothesis),
        "meteor": sentence_meteor(reference, hypothesis),
        "reference_source": reference_source,
    }

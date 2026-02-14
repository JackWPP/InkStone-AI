# Paper Preparation Checklist (Execution-bound)

## Problem and Claims

- Define hypotheses H1/H2/H3 with measurable acceptance criteria.
- Ensure each claim maps to at least one figure/table and one metric.

## Method

- Freeze five-dimension definitions and OV weighting.
- Freeze persona profiles and prompt versions.
- Version all prompt files under `configs/prompts/`.

## Experiments and Ablation

- Record run seed, model versions, prompt versions, and reference source.
- Run system comparison A/B/C with same eval set.
- Add ablation plan: with/without ICL, with different K values.

## Reproducibility

- Keep one-command execution path valid.
- Ensure all produced figures are generated from code, not manual edits.
- Save logs and methodology docs per run.

## Figures and Tables

- Fig1 distribution, Fig2 human-model correlation, Fig3 radar, Fig4 heatmap.
- Include correlation coefficients and clear caption-ready notes.

## Artifact Readiness

- Keep outputs in `reports/` and `docs/methodology/`.
- Do not publish raw copyrighted full text.

# INKSTONE-AI Implementation Plan (Phase 1)

## Milestone M1: Skeleton + One-command runnable baseline

1. Create required repository structure from SPEC section 10.
2. Implement pipeline orchestrator and module stubs with deterministic outputs.
3. Generate mandatory artifacts in required paths.
4. Add bootstrap/preflight/download scripts.

## Milestone M2: Real data ingestion (CMDAG/CMC)

1. Replace seed dataset with real automatic download and normalization.
2. Implement stratified sampling and frozen eval set.
3. Add optional books extraction route.

## Milestone M3: Real translation and judge integration

1. Implement HF NMT models for System A/B.
2. Implement multi-provider LLM adapter for System C and judge modules.
3. Enable ICL few-shot injection in standard judge.

## Milestone M4: Statistics and publication-grade outputs

1. Add bootstrap confidence intervals.
2. Strengthen correlation and significance reporting.
3. Improve figures and report templates for direct thesis insertion.

## Milestone M5: Testing and reproducibility hardening

1. Add unit tests for core modules and schemas.
2. Add smoke test for full run_all path.
3. Pin reproducibility details in logs and methodology docs.

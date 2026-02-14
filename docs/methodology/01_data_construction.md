# Data Construction

本次默认使用内置种子样本流程（后续会接入 CMDAG/CMC 自动下载）。

## Metaphor Tagger Prompt

```text
Classify the Chinese sentence into one metaphor type:
simile, implicit, personification, synesthesia, cultural_allusion, dead_conventional, mixed_other.
Return strict JSON: {"metaphor_type":"...","cultural_load":"low|medium|high"}

```

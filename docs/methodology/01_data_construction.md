# 数据构建

本次默认使用内置种子样本流程（后续会接入 CMDAG/CMC 自动下载）。

## 隐喻标注提示词

```text
请将中文句子判定为一个隐喻类别：
simile, implicit, personification, synesthesia, cultural_allusion, dead_conventional, mixed_other。
请仅返回严格 JSON：{"metaphor_type":"...","cultural_load":"low|medium|high"}

```

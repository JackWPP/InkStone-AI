# 数据构建

本次流程优先解析外部数据（CMDAG/CMC 目录），并支持 books 可选补充，最后以 seed 样本兜底。

## 隐喻标注提示词

```text
请将中文句子判定为一个隐喻类别：
simile, implicit, personification, synesthesia, cultural_allusion, dead_conventional, mixed_other。
请仅返回严格 JSON：{"metaphor_type":"...","cultural_load":"low|medium|high"}

```

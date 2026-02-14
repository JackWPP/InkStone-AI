from __future__ import annotations

import importlib
import json
import os
from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class LLMConfig:
    provider: str
    model: str
    base_url: str | None
    api_key_env: str
    temperature: float = 0.2
    timeout: float = 60.0
    max_retries: int = 1


def llm_config_from_dict(cfg: dict[str, Any]) -> LLMConfig:
    return LLMConfig(
        provider=str(cfg.get("provider", "openai_compatible")),
        model=str(cfg.get("model", "")),
        base_url=str(cfg.get("base_url")) if cfg.get("base_url") else None,
        api_key_env=str(cfg.get("api_key_env", "OPENAI_API_KEY")),
        temperature=float(cfg.get("temperature", 0.2)),
        timeout=float(cfg.get("timeout", 60.0)),
        max_retries=int(cfg.get("max_retries", 1)),
    )


def _build_client(config: LLMConfig) -> Any:
    if config.provider != "openai_compatible":
        raise ValueError(f"暂不支持的 provider: {config.provider}")
    key = os.getenv(config.api_key_env, "")
    is_local = bool(config.base_url and "localhost" in config.base_url)
    if not key and is_local:
        key = "lm-studio"
    if not key:
        return None
    openai_mod = importlib.import_module("openai")
    client_cls = getattr(openai_mod, "OpenAI")
    kwargs: dict[str, Any] = {"api_key": key, "timeout": config.timeout}
    if config.base_url:
        kwargs["base_url"] = config.base_url
    return client_cls(**kwargs)


def chat_text(config: LLMConfig, system_prompt: str, user_prompt: str) -> str | None:
    attempts = max(1, int(config.max_retries) + 1)
    for _ in range(attempts):
        try:
            client = _build_client(config)
            if client is None:
                return None
            response = client.chat.completions.create(
                model=config.model,
                temperature=config.temperature,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            content = response.choices[0].message.content
            if content is None:
                continue
            return str(content).strip()
        except Exception:
            continue
    return None


def chat_json(
    config: LLMConfig,
    system_prompt: str,
    user_prompt: str,
    required_fields: list[str],
) -> dict[str, Any] | None:
    text = chat_text(config, system_prompt, user_prompt)
    if text is None:
        return None
    try:
        obj = json.loads(text)
    except Exception:
        return None
    if not isinstance(obj, dict):
        return None
    for field in required_fields:
        if field not in obj:
            return None
    return obj

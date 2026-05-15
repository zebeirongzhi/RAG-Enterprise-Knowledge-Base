import re
import logging
from openai import OpenAI

from config import settings

logger = logging.getLogger(__name__)

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = OpenAI(api_key=settings.deepseek_api_key, base_url=settings.deepseek_base_url)
    return _client


def detect_language(text: str) -> str:
    """Return 'zh' if CJK character ratio > 40%, otherwise 'en'."""
    if not text or not text.strip():
        return "en"
    cjk = 0
    for ch in text:
        cp = ord(ch)
        if (0x4E00 <= cp <= 0x9FFF or 0x3400 <= cp <= 0x4DBF or
            0x20000 <= cp <= 0x2A6DF or 0xF900 <= cp <= 0xFAFF or
            0x2F800 <= cp <= 0x2FA1F):
            cjk += 1
    ratio = cjk / len(text)
    logger.info(f"Language detection: CJK ratio={ratio:.2%} ({cjk}/{len(text)} chars)")
    return "zh" if ratio > 0.4 else "en"


def _split_for_translation(text: str, max_chars: int = 3000) -> list[str]:
    """Split text at paragraph boundaries to stay under max_chars per chunk."""
    paragraphs = text.split("\n\n")
    chunks = []
    current = ""
    for para in paragraphs:
        if len(current) + len(para) + 2 <= max_chars:
            current = (current + "\n\n" + para) if current else para
        else:
            if current:
                chunks.append(current)
            current = para if len(para) <= max_chars else para[:max_chars]
    if current:
        chunks.append(current)
    return chunks


def translate_to_chinese(text: str) -> str:
    """Translate English text to Chinese using DeepSeek API."""
    client = _get_client()

    chunks = _split_for_translation(text)
    if len(chunks) == 1:
        resp = client.chat.completions.create(
            model=settings.deepseek_model,
            messages=[
                {"role": "system", "content": "You are a professional translator. Translate the following English text to Chinese accurately. Preserve formatting (markdown, line breaks, lists). Keep technical terms consistent. Output ONLY the Chinese translation, no explanations."},
                {"role": "user", "content": chunks[0]},
            ],
            temperature=0.1,
            max_tokens=4096,
        )
        return resp.choices[0].message.content.strip()

    translated_parts = []
    for i, chunk in enumerate(chunks):
        logger.info(f"Translating chunk {i+1}/{len(chunks)} ({len(chunk)} chars)")
        resp = client.chat.completions.create(
            model=settings.deepseek_model,
            messages=[
                {"role": "system", "content": "You are a professional translator. Translate the following English text to Chinese accurately. Preserve formatting (markdown, line breaks, lists). Keep technical terms consistent. This is part of a larger document. Output ONLY the Chinese translation, no explanations."},
                {"role": "user", "content": chunk},
            ],
            temperature=0.1,
            max_tokens=4096,
        )
        translated_parts.append(resp.choices[0].message.content.strip())
    return "\n\n".join(translated_parts)

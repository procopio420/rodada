"""Derived label used only for literal, accent-insensitive Tab search."""
import re
import unicodedata


def normalize_tab_label(value: str) -> str:
    text = unicodedata.normalize("NFKC", value).casefold()
    text = "".join(char for char in unicodedata.normalize("NFKD", text) if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", text).strip()

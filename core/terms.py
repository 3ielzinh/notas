# core/terms.py
from typing import Dict, List, Optional, Iterable
from .db import fetch_terms_for_sanitization

def get_terms_for_sanitization(categories: Optional[Iterable[str]] = None) -> Dict[str, List[str]]:
    """
    Ponto único para o restante do app pegar os termos (sempre do banco).
    """
    return fetch_terms_for_sanitization(categories)

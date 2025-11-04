# core/paths.py
from pathlib import Path
from typing import Optional
import os

# Caminho base flexível
# 1) Primeiro tenta variável de ambiente PREVIDENCIA_NOTAS
# 2) Se não existir, assume que a pasta "NOTAS" está no mesmo nível do projeto
BASE_NOTAS_DIR = Path(
    os.environ.get("PREVIDENCIA_NOTAS", Path(__file__).resolve().parent.parent / "NOTAS")
)

PREFERRED_DIR = BASE_NOTAS_DIR / "NOTAS_REVISADAS"

# Pastas legadas por ano (fallback)
YEAR_START, YEAR_END = 2020, 2025
LEGACY_DIRS = [BASE_NOTAS_DIR / f"NOTAS TÉCNICAS {y}" for y in range(YEAR_START, YEAR_END + 1)]


def resolve_pdf_path(filename_or_path: str) -> Optional[Path]:
    """
    Resolve o caminho do PDF dando prioridade à pasta NOTAS_REVISADAS.
    Aceita: nome do arquivo (ex.: "NOTA ... .pdf") OU caminho completo anterior.
    Retorna Path existente ou None.
    """
    p = Path(filename_or_path)

    # Se veio caminho completo e existe na pasta nova com o MESMO nome, preferimos o novo.
    candidate = PREFERRED_DIR / p.name
    if candidate.exists():
        return candidate

    # Se passou caminho completo e ele mesmo existe (legado)
    if p.exists() and p.suffix.lower() == ".pdf":
        return p

    # Tenta encontrar pelo nome nas pastas legadas
    for d in LEGACY_DIRS:
        legacy = d / p.name
        if legacy.exists():
            return legacy

    # Por fim, tenta se for relativo existente
    if p.is_file():
        return p

    return None


def url_safe_name(p: Path) -> str:
    """Utilitário para logs/UI."""
    try:
        return str(p.relative_to(BASE_NOTAS_DIR))
    except Exception:
        return p.name

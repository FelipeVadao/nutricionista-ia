from teste_personal.config import PROJECT_ROOT

PERFIL_PATH = PROJECT_ROOT / "Prompt" / "perfil.md"


def carregar_instrucoes() -> str:
    return PERFIL_PATH.read_text(encoding="utf-8")

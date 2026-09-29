from datetime import date
from pathlib import Path
from typing import Callable

from agno.knowledge.knowledge import Knowledge

from teste_personal.config import NOME_ARQUIVO_DIETA, PLANO_DE_DIETA_DIR


def _caminho_disponivel(pasta: Path, hoje: date) -> Path:
    base = pasta / NOME_ARQUIVO_DIETA.format(data=hoje.strftime("%d_%m_%Y"))
    caminho, n = base, 2
    while caminho.exists():
        caminho = base.with_name(f"{base.stem}_v{n}{base.suffix}")
        n += 1
    return caminho


def criar_tool_salvar_dieta(knowledge: Knowledge, pasta: Path = PLANO_DE_DIETA_DIR) -> Callable[..., str]:
    def salvar_dieta_gerada(conteudo_markdown: str, resumo: str) -> str:
        """Salva um plano alimentar FINALIZADO em Plano_de_Dieta/ e o indexa na base de conhecimento (RAG),
        para que sirva de histórico/contexto nas próximas conversas.
        Chame apenas quando o usuário aprovar ou pedir a versão final da dieta — não para rascunhos.

        Args:
            conteudo_markdown: O plano alimentar completo em Markdown (refeições, quantidades, metas calóricas,
                cálculos usados e fontes citadas).
            resumo: Uma frase descrevendo o objetivo/mudança principal desta dieta.
        """
        hoje = date.today()
        caminho = _caminho_disponivel(pasta, hoje)
        cabecalho = f"# Plano Alimentar gerado pelo agente — {hoje.strftime('%d/%m/%Y')}\n\n> {resumo}\n\n"
        caminho.write_text(cabecalho + conteudo_markdown, encoding="utf-8")
        knowledge.insert(
            path=str(caminho),
            name=caminho.stem,
            metadata={"origem": "agente", "data": hoje.isoformat()},
        )
        return f"Dieta salva em '{caminho.name}' e indexada na base de conhecimento."

    return salvar_dieta_gerada

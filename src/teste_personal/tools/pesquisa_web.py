import json
import os
from typing import Callable, Sequence
from urllib.parse import urlparse

from agno.run.base import RunContext
from tavily import TavilyClient


def dominio_confiavel(url: str, dominios: Sequence[str]) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return any(host == d or host.endswith("." + d) for d in dominios)


def criar_tool_pesquisa_web(dominios: Sequence[str], limite_por_resposta: int) -> Callable[..., str]:
    client = TavilyClient(api_key=os.environ.get("TAVILY_API_KEY"))
    uso = {"run_id": None, "pesquisas": 0}

    def pesquisar_web(consulta: str, run_context: RunContext, max_resultados: int = 5) -> str:
        """Pesquisa na Web restrita a domínios confiáveis de saúde e nutrição (órgãos oficiais,
        universidades, publicações científicas e bases de dados nutricionais).
        Retorna título, URL e trecho de cada página. Só use dados que estejam escritos no trecho retornado,
        e sempre cite a URL.

        Há um limite de pesquisas por resposta: planeje as consultas antes e agrupe vários alimentos
        ou dúvidas na mesma consulta.

        Args:
            consulta: O que pesquisar. Pode agrupar itens (ex.: "TACO composição arroz cozido feijão frango batata-doce").
            max_resultados: Número máximo de resultados (1 a 10).
        """
        if run_context.run_id != uso["run_id"]:
            uso.update(run_id=run_context.run_id, pesquisas=0)
        if uso["pesquisas"] >= limite_por_resposta:
            return (
                f"Limite de {limite_por_resposta} pesquisas nesta resposta atingido. Não pesquise mais: "
                "responda com as fontes já obtidas e indique explicitamente o que ficou sem fonte."
            )
        uso["pesquisas"] += 1

        resposta = client.search(
            query=consulta,
            search_depth="advanced",
            max_results=max(1, min(max_resultados, 10)),
            include_domains=list(dominios),
            # Sem "restrict" o Tavily trata a lista como preferência e completa com qualquer site.
            include_domains_mode="restrict",
            include_answer=False,
        )
        resultados = [
            {"titulo": r["title"], "url": r["url"], "trecho": r["content"]}
            for r in resposta.get("results", [])
            if dominio_confiavel(r["url"], dominios)
        ]
        restantes = limite_por_resposta - uso["pesquisas"]
        if not resultados:
            return (
                "Nenhum resultado de fonte confiável encontrado. Não use dados da Web para esta pergunta. "
                f"Pesquisas restantes nesta resposta: {restantes}."
            )
        return json.dumps(
            {
                "consulta": consulta,
                "resultados": resultados,
                "descartados_fora_da_lista": len(resposta.get("results", [])) - len(resultados),
                "pesquisas_restantes_nesta_resposta": restantes,
            },
            ensure_ascii=False,
        )

    return pesquisar_web

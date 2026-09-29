from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.knowledge.knowledge import Knowledge
from agno.models.anthropic import Claude

from teste_personal.config import (
    MAX_PESQUISAS_WEB_POR_RESPOSTA,
    MAX_TOKENS,
    MODEL_ID,
    TRUSTED_DOMAINS,
    USER_ID,
)
from teste_personal.prompts import carregar_instrucoes
from teste_personal.tools import (
    calcular_taxa_metabolica_basal,
    consultar_taco,
    criar_tool_pesquisa_web,
    criar_tool_salvar_dieta,
)


def build_agent(db: SqliteDb, knowledge: Knowledge) -> Agent:
    return Agent(
        name="Nutricionista",
        model=Claude(id=MODEL_ID, max_tokens=MAX_TOKENS),
        instructions=carregar_instrucoes(),
        user_id=USER_ID,
        db=db,
        knowledge=knowledge,
        search_knowledge=True,
        tools=[
            calcular_taxa_metabolica_basal,
            consultar_taco,
            criar_tool_salvar_dieta(knowledge),
            criar_tool_pesquisa_web(TRUSTED_DOMAINS, MAX_PESQUISAS_WEB_POR_RESPOSTA),
        ],
        enable_agentic_memory=True,
        add_history_to_context=True,
        num_history_runs=10,
        add_datetime_to_context=True,
        timezone_identifier="America/Sao_Paulo",
        markdown=True,
    )

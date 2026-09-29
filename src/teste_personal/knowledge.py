from agno.db.sqlite import SqliteDb
from agno.knowledge.embedder.fastembed import FastEmbedEmbedder
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.lancedb import LanceDb

from teste_personal.config import (
    EMBEDDER_DIMENSIONS,
    EMBEDDER_MODEL_ID,
    LANCEDB_URI,
    PLANO_DE_DIETA_DIR,
)


def build_knowledge(db: SqliteDb) -> Knowledge:
    return Knowledge(
        name="Plano_de_Dieta",
        description="Histórico de planos alimentares do usuário e materiais de referência sobre nutrição/metabolismo.",
        vector_db=LanceDb(
            uri=LANCEDB_URI,
            table_name="plano_de_dieta",
            embedder=FastEmbedEmbedder(id=EMBEDDER_MODEL_ID, dimensions=EMBEDDER_DIMENSIONS),
        ),
        contents_db=db,
        max_results=8,
    )


def sincronizar_base(knowledge: Knowledge) -> None:
    """Indexa arquivos novos de Plano_de_Dieta/; os já indexados são ignorados."""
    knowledge.insert(
        path=str(PLANO_DE_DIETA_DIR),
        include=["*.pdf", "*.md"],
        skip_if_exists=True,
    )

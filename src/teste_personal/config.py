import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

PLANO_DE_DIETA_DIR = PROJECT_ROOT / "Plano_de_Dieta"
# A TACO não entra no índice vetorial: busca semântica não acha nomes exatos numa tabela.
# scripts/gerar_taco.py converte o PDF em .txt, lido pela ferramenta consultar_taco.
TACO_PDF = PROJECT_ROOT / "Referencias" / "TACO_4a_edicao_ampliada_e_revisada.pdf"
TACO_TXT = PLANO_DE_DIETA_DIR / "TACO_composicao_centesimal.txt"
DATA_DIR = PROJECT_ROOT / "data"

# Por padrão o FastEmbed guarda o modelo na pasta Temp do sistema, que o Windows pode limpar.
os.environ.setdefault("FASTEMBED_CACHE_PATH", str(DATA_DIR / "fastembed_cache"))
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
LANCEDB_URI = str(DATA_DIR / "lancedb")
SQLITE_FILE = str(DATA_DIR / "nutricionista.db")

MODEL_ID = "claude-sonnet-5"
# O raciocínio (adaptive thinking, ligado por padrão no Sonnet 5) consome o mesmo limite do texto.
# O padrão do Agno (8192) se esgotava só no raciocínio e a dieta saía vazia. Exige streaming.
MAX_TOKENS = 64000
# Multilíngue: os planos alimentares estão em PT-BR e o modelo padrão do FastEmbed é só inglês.
EMBEDDER_MODEL_ID = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
EMBEDDER_DIMENSIONS = 384

USER_ID = "felipe"
MAX_PESQUISAS_WEB_POR_RESPOSTA = 6
NOME_ARQUIVO_DIETA = "Plano Alimentar_Vadão_{data}.md"

TRUSTED_DOMAINS = [
    "gov.br",
    "saude.gov.br",
    "anvisa.gov.br",
    "cfn.org.br",
    "sbem.org.br",
    "abeso.org.br",
    "sban.org.br",
    "scielo.br",
    "tbca.net.br",
    "unicamp.br",
    "usp.br",
    "ncbi.nlm.nih.gov",
    "nih.gov",
    "who.int",
    "fao.org",
    "usda.gov",
    "eatright.org",
    "mayoclinic.org",
    "health.harvard.edu",
    "hsph.harvard.edu",
    "examine.com",
]

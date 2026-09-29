# Nutricionista IA

Agente de IA pessoal para planejamento e acompanhamento de dietas, construído com [Agno](https://github.com/agno-agi/agno) e o modelo Claude (Anthropic). Roda por linha de comando, mantém histórico de conversas e planos alimentares em uma base local, e só usa dados com origem verificável (tabela TACO, documentos do usuário ou pesquisa web restrita a domínios confiáveis) — nunca inventa valores nutricionais.

## Funcionalidades

- **Cálculo de TMB/GET**: Taxa Metabólica Basal (fórmula de Harris-Benedict revisada) e Gasto Energético Total, via ferramenta determinística — o agente nunca estima esses valores "de cabeça".
- **Consulta à tabela TACO**: composição nutricional (kcal, proteína, lipídeos, carboidrato, fibra, colesterol, umidade) a partir da Tabela Brasileira de Composição de Alimentos (NEPA/UNICAMP), extraída localmente do PDF de referência.
- **Pesquisa na Web restrita**: busca (via Tavily) limitada a uma lista de domínios confiáveis (órgãos de saúde, universidades, bases científicas), com limite de consultas por resposta.
- **Base de conhecimento (RAG)**: indexa os planos alimentares em `Plano_de_Dieta/` (PDF/Markdown) em um vetor store local, usado para manter histórico e contexto entre conversas.
- **Memória e histórico**: memória agentic e histórico de execuções persistidos em SQLite, para continuidade entre sessões.
- **Geração de dietas**: monta o plano em Markdown num formato fixo (objetivo, dados do usuário, cálculo energético, macros, refeições, fontes) e salva a versão final aprovada em `Plano_de_Dieta/`, reindexando-a automaticamente.

## Arquitetura

```
src/teste_personal/
├── agent.py         # monta o Agent (modelo, tools, memória, histórico)
├── config.py        # paths, IDs de modelo/embedder, domínios confiáveis
├── knowledge.py      # base RAG (LanceDB + FastEmbed) sobre Plano_de_Dieta/
├── prompts.py        # carrega as instruções do agente (Prompt/perfil.md)
├── __init__.py        # loop de chat no terminal (main)
└── tools/
    ├── bmr.py          # cálculo de TMB/GET (Harris-Benedict)
    ├── taco.py          # busca na tabela TACO local (.txt)
    ├── pesquisa_web.py  # busca web restrita a domínios confiáveis (Tavily)
    └── salvar_dieta.py  # salva e indexa a dieta final aprovada

scripts/gerar_taco.py  # converte o PDF da TACO em um .txt legível pela tool `consultar_taco`
Prompt/perfil.md        # prompt de sistema: papel, regras e formato de saída do agente
Plano_de_Dieta/          # histórico de dietas do usuário + fonte da tabela TACO em texto
Referencias/             # PDF de referência da TACO (fonte de scripts/gerar_taco.py)
data/                    # SQLite + índice vetorial (gerado, não versionado)
```

Fluxo: o texto de `Prompt/perfil.md` define as regras do agente (fontes válidas, hierarquia de prioridade, formato da dieta). O agente sempre prioriza, nesta ordem: dados atuais informados pelo usuário → cálculos determinísticos → base RAG (histórico) → pesquisa web.

## Pré-requisitos

- Python (versão fixada em [.python-version](.python-version))
- [uv](https://docs.astral.sh/uv/)
- Chaves de API:
  - `ANTHROPIC_API_KEY` — modelo Claude
  - `TAVILY_API_KEY` — pesquisa web

## Configuração

1. Instale as dependências:

   ```powershell
   uv sync
   ```

2. Crie um arquivo `.env` na raiz do projeto com as chaves de API:

   ```env
   ANTHROPIC_API_KEY=sua-chave
   TAVILY_API_KEY=sua-chave
   ```

3. (Opcional) Gere o `.txt` da tabela TACO a partir do PDF de referência — só é necessário se [Plano_de_Dieta/TACO_composicao_centesimal.txt](Plano_de_Dieta/TACO_composicao_centesimal.txt) não existir ou precisar ser regenerado:

   ```powershell
   uv run python scripts/gerar_taco.py
   ```

## Uso

```powershell
uv run teste-personal
```

Na primeira execução, o conteúdo de `Plano_de_Dieta/` é indexado na base de conhecimento local (`data/`, gerado e ignorado pelo git). O agente então inicia um chat no terminal; digite `sair`, `exit` ou `quit` para encerrar.

## Personalização

- **Regras e formato do agente**: edite [Prompt/perfil.md](Prompt/perfil.md).
- **Domínios confiáveis para pesquisa web, limites e IDs de modelo**: edite [src/teste_personal/config.py](src/teste_personal/config.py).
- **Histórico de dietas**: adicione PDFs/Markdown em `Plano_de_Dieta/` — são indexados automaticamente na próxima execução (arquivos já indexados são ignorados).

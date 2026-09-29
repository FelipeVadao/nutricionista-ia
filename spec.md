# Especificação — Nutricionista IA

## 1. Visão geral

Agente de IA pessoal (uso individual, via linha de comando) para planejamento e acompanhamento
de dietas. Constrói e atualiza planos alimentares personalizados, mantém histórico de conversas
e de dietas anteriores, e é restrito a usar apenas dados com origem verificável — nunca infere ou
"chuta" valores nutricionais, cálculos ou referências.

- **Stack**: Python 3.12+, [Agno](https://github.com/agno-agi/agno) como framework de agente,
  modelo Claude (Anthropic) via `agno.models.anthropic.Claude`.
- **Execução**: `uv run teste-personal` — loop de chat interativo no terminal, sem interface
  gráfica ou API HTTP.
- **Persistência local**: SQLite (histórico de execuções + memória agentic) e LanceDB
  (índice vetorial da base de conhecimento), ambos em `data/` (gerado, não versionado).
- **Idioma**: toda interação e todo conteúdo gerado é em Português do Brasil.

## 2. Objetivos

1. Calcular TMB (Taxa Metabólica Basal) e GET (Gasto Energético Total) de forma determinística.
2. Consultar composição nutricional de alimentos na Tabela TACO (fonte primária).
3. Buscar informações nutricionais/científicas atualizadas na Web, restrito a domínios confiáveis,
   quando a TACO e a base local não bastarem.
4. Montar e atualizar planos alimentares em Markdown, num formato fixo, usando o histórico do
   usuário como contexto.
5. Persistir a versão final aprovada de cada dieta e reindexá-la automaticamente, para servir de
   histórico em conversas futuras.
6. Nunca apresentar como fato um valor nutricional, cálculo ou referência que não venha de uma das
   três fontes autorizadas (ver seção 4).

## 3. Fora de escopo

- Múltiplos usuários / multi-tenant (o agente é pessoal, `USER_ID` fixo em `config.py`).
- Interface web, API HTTP ou aplicativo mobile.
- Substituição de acompanhamento nutricional profissional — é uma ferramenta de apoio pessoal.
- Edição/exclusão de dietas já salvas pelo próprio agente (só cria novas versões).
- Autenticação, autorização ou controle de acesso (execução local, single-user).

## 4. Fontes de dados autorizadas

O agente só pode fundamentar respostas nutricionais em três fontes, nesta ordem de prioridade
quando houver conflito:

1. **Dados fornecidos pelo usuário na conversa atual** (têm prioridade sobre qualquer histórico).
2. **Cálculos determinísticos** (fórmulas fixas, nunca estimados "de cabeça" pelo modelo).
3. **Base RAG** (histórico de dietas e documentos em `Plano_de_Dieta/`, indexados em LanceDB).
4. **Pesquisa Web restrita** (apenas quando as anteriores não cobrem a necessidade).

Regra absoluta: se a informação não estiver disponível em nenhuma fonte autorizada, o agente deve
declarar isso explicitamente e pedir o dado ao usuário — nunca preencher com um valor plausível.

## 5. Funcionalidades e ferramentas (tools)

| Ferramenta | Arquivo | Responsabilidade |
|---|---|---|
| `calcular_taxa_metabolica_basal` | `src/teste_personal/tools/bmr.py` | TMB via Harris-Benedict revisada (Roza & Shizgal, 1984) e GET = TMB × fator de atividade. Valida faixas de peso (20–400 kg), altura (100–250 cm) e idade (10–120 anos); levanta `ValueError` fora delas. |
| `consultar_taco` | `src/teste_personal/tools/taco.py` | Busca textual (normalizada, sem acento, tolerante a plural/gênero) na Tabela TACO local (`.txt` gerado do PDF), por 100 g de alimento. Aceita múltiplos alimentos numa chamada; retorna até 5 correspondências por alimento com nota de similaridade mínima. |
| `pesquisar_web` (via `criar_tool_pesquisa_web`) | `src/teste_personal/tools/pesquisa_web.py` | Busca via Tavily restrita a `TRUSTED_DOMAINS` (`include_domains_mode="restrict"`), com filtro pós-busca por domínio. Limite de `MAX_PESQUISAS_WEB_POR_RESPOSTA` (6) buscas por resposta, contado por `run_id`. |
| `salvar_dieta_gerada` (via `criar_tool_salvar_dieta`) | `src/teste_personal/tools/salvar_dieta.py` | Salva o Markdown final em `Plano_de_Dieta/` (nome com data, versionado com sufixo `_vN` em caso de colisão) e indexa o arquivo na base de conhecimento. Só deve ser chamada para versões aprovadas, não rascunhos. |
| `search_knowledge_base` (nativa do Agno) | `src/teste_personal/knowledge.py` | Busca semântica (RAG) sobre PDFs/Markdown de `Plano_de_Dieta/`, via LanceDB + FastEmbed multilíngue. |

### 5.1 Cálculo de TMB/GET

- Fórmula fixa de Harris-Benedict revisada (sexo, peso, altura, idade).
- Fatores de atividade fixos: `sedentario=1.2`, `leve=1.375`, `moderado=1.55`, `intenso=1.725`,
  `muito_intenso=1.9`.
- O agente não deve reaproveitar peso/idade de planos antigos sem confirmar com o usuário na
  conversa atual.

### 5.2 Consulta TACO

- Fonte primária para composição nutricional de alimentos (kcal, proteína, lipídeos, carboidrato,
  fibra, colesterol, umidade).
- A tabela não é indexada no vetor store (busca semântica não é confiável para nomes exatos);
  em vez disso, é convertida de PDF para `.txt` por `scripts/gerar_taco.py` e consultada por
  correspondência de termos.
- O agente deve escolher o item com o preparo correto (cru/cozido/grelhado) e citar o número
  TACO; nunca adaptar valores de um item diferente do pedido.
- Se o alimento não constar na TACO, o agente deve informar isso antes de considerar Web ou
  histórico do usuário (ex.: rótulo de suplemento).

### 5.3 Pesquisa Web restrita

- Lista fixa de domínios confiáveis em `TRUSTED_DOMAINS` (`config.py`): órgãos governamentais de
  saúde, sociedades médicas/nutricionais, universidades, bases científicas (SciELO, NCBI, WHO,
  FAO, USDA) e referências reconhecidas (Mayo Clinic, Harvard Health, Examine.com).
- Resultados fora da lista são descartados mesmo que o provedor os retorne.
- Limite de 6 pesquisas por resposta (reiniciado a cada novo `run_id`); ao esgotar, o agente deve
  responder com o que já tem e marcar explicitamente o que ficou sem fonte.
- Valores quantitativos (calorias, macros, recomendações) devem ser cruzados em ao menos duas
  fontes independentes quando possível; divergências devem ser expostas ao usuário, não resolvidas
  silenciosamente.
- Citação obrigatória no formato `[Título da página](URL)`, e apenas URLs que de fato apareceram
  no retorno da ferramenta.

### 5.4 Base de conhecimento (RAG)

- Indexa `Plano_de_Dieta/*.pdf` e `*.md` em LanceDB (tabela `plano_de_dieta`), usando
  `FastEmbedEmbedder` multilíngue (`paraphrase-multilingual-MiniLM-L12-v2`, 384 dimensões) —
  necessário porque os planos estão em PT-BR.
- Sincronização (`sincronizar_base`) roda a cada início do programa, com `skip_if_exists=True`
  (arquivos já indexados não são reprocessados).
- Serve como contexto de continuidade entre sessões: refeições anteriores, preferências,
  restrições, evolução dos planos ao longo do tempo — mas informação histórica nunca sobrepõe
  dado atual informado pelo usuário.

### 5.5 Memória e histórico de conversa

- `enable_agentic_memory=True`: memória agentic persistida no SQLite (`data/nutricionista.db`).
- `add_history_to_context=True`, `num_history_runs=10`: as últimas 10 execuções entram no
  contexto de cada nova mensagem.
- `add_datetime_to_context=True`, timezone `America/Sao_Paulo`.

### 5.6 Geração e persistência de dietas

- Formato de saída obrigatório em Markdown, com seções fixas nesta ordem (ver `Prompt/perfil.md`
  seção 10): Objetivo, Dados do Usuário, Cálculo Energético, Distribuição de Macronutrientes,
  Refeições (com substituições), Mudanças em relação ao plano anterior, Observações, Fontes.
  Seções sem informação devem conter "Não informado" / "Não se aplica" em vez de serem omitidas.
- A resposta que entrega uma dieta deve começar diretamente pelo título `# Plano Alimentar — ...`,
  sem comentários de raciocínio antes ou entre chamadas de ferramenta.
- Persistência apenas quando o usuário aprova ou pede a versão final (`salvar_dieta_gerada`):
  grava em `Plano_de_Dieta/Plano Alimentar_Vadão_<DD_MM_AAAA>.md` (colisão de data gera
  `_v2`, `_v3`, ...) e reindexa o arquivo na base de conhecimento imediatamente.

## 6. Regras de negócio (resumo do prompt de sistema)

Fonte completa: [`Prompt/perfil.md`](Prompt/perfil.md). Resumo normativo:

1. **Nunca inventar** informações, valores nutricionais, alimentos, recomendações, referências ou
   resultados de cálculo — admitir a falta de dado é preferível a uma estimativa arbitrária.
2. **Hierarquia de fontes** em caso de conflito: dado atual do usuário > cálculo determinístico >
   base RAG (histórico) > pesquisa Web.
3. **Histórico não é verdade atual**: dados de planos antigos só valem como referência, nunca como
   substituto de confirmação com o usuário.
4. Toda dieta nova ou atualizada segue o **formato de Markdown fixo** (seção 5.6); toda outra
   interação (perguntas, cálculos isolados) responde em Markdown livre.
5. Sempre citar a origem de cada valor: número/nome do item TACO, documento da base, ou
   `[Título](URL)` para Web.

## 7. Configuração e ambiente

Definido em `src/teste_personal/config.py`, carregado de `.env` (não versionado):

| Variável / constante | Descrição |
|---|---|
| `ANTHROPIC_API_KEY` (env) | Chave da API Claude (obrigatória). |
| `TAVILY_API_KEY` (env) | Chave da API Tavily para pesquisa Web (obrigatória). |
| `MODEL_ID` | `claude-sonnet-5`. |
| `MAX_TOKENS` | `64000` — necessário porque o raciocínio adaptativo do Sonnet 5 consome o mesmo orçamento de tokens que a resposta; o padrão do Agno (8192) esgotava só no raciocínio. |
| `EMBEDDER_MODEL_ID` / `EMBEDDER_DIMENSIONS` | Embedder multilíngue FastEmbed, 384 dimensões. |
| `USER_ID` | `"felipe"` — fixo, uso pessoal. |
| `MAX_PESQUISAS_WEB_POR_RESPOSTA` | `6`. |
| `TRUSTED_DOMAINS` | Lista fixa de domínios (ver seção 5.3). |
| `PLANO_DE_DIETA_DIR`, `TACO_PDF`, `TACO_TXT`, `DATA_DIR` | Paths derivados de `PROJECT_ROOT`. |

Pré-requisitos: Python na versão fixada em `.python-version`, gerenciador `uv`. Geração do
`.txt` da TACO a partir do PDF de referência via `scripts/gerar_taco.py` (só necessário se o
`.txt` não existir ou precisar ser regenerado).

## 8. Estrutura de diretórios

```
src/teste_personal/
├── agent.py          # monta o Agent (modelo, tools, memória, histórico)
├── config.py         # paths, IDs de modelo/embedder, domínios confiáveis
├── knowledge.py       # base RAG (LanceDB + FastEmbed) sobre Plano_de_Dieta/
├── prompts.py         # carrega Prompt/perfil.md
├── __init__.py         # loop de chat no terminal (main)
└── tools/
    ├── bmr.py           # TMB/GET (Harris-Benedict)
    ├── taco.py           # busca na tabela TACO local (.txt)
    ├── pesquisa_web.py   # busca web restrita a domínios confiáveis (Tavily)
    └── salvar_dieta.py   # salva e indexa a dieta final aprovada

scripts/gerar_taco.py   # converte o PDF da TACO em .txt legível pela tool consultar_taco
Prompt/perfil.md         # prompt de sistema (papel, regras, formato de saída)
Plano_de_Dieta/           # histórico de dietas do usuário + TACO em texto
Referencias/              # PDF de referência da TACO
data/                     # SQLite + índice vetorial (gerado, não versionado)
```

## 9. Requisitos não funcionais

- **Rastreabilidade**: toda afirmação nutricional deve ser rastreável até TACO, cálculo
  determinístico, documento da base ou URL específica retornada pela pesquisa.
- **Resiliência a limite de tokens**: `__init__.py` detecta resposta vazia (provável esgotamento
  de tokens no raciocínio) e avisa o usuário para reformular, em vez de falhar silenciosamente.
- **Custo/latência de pesquisa Web**: limitar e contar buscas por execução (`run_id`) para evitar
  uso excessivo da API Tavily numa única resposta.
- **Cache local de embeddings**: `FASTEMBED_CACHE_PATH` fixado em `data/fastembed_cache` (fora do
  diretório Temp do Windows, que pode ser limpo pelo sistema).
- **Idempotência de indexação**: reindexação da base (`sincronizar_base`) ignora arquivos já
  indexados (`skip_if_exists=True`), permitindo rodar a cada início sem custo de reprocessamento.

## 10. Riscos e limitações conhecidas

- Busca na TACO é por correspondência de termos (não semântica) — sensível à forma como o
  alimento é descrito; falso-negativo é preferível a falso-positivo (nota mínima de 0.5 e proibição
  de adaptar valores de outro item).
- Restrição de domínios da pesquisa Web depende de `include_domains_mode="restrict"` do Tavily e
  de um filtro pós-busca redundante — mudanças na API do provedor podem exigir revalidação.
- Sem versionamento/diff entre planos: cada dieta salva é um arquivo novo; comparações "o que
  mudou" dependem do agente ler o histórico via RAG, não de um mecanismo estruturado.
- Uso single-user: não há isolamento de dados caso o projeto evolua para múltiplos usuários.

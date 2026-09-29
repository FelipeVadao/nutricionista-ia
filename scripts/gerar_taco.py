"""Converte a Tabela 1 da TACO (PDF) em um .txt com uma linha autoexplicativa por alimento.

Uso: uv run python scripts/gerar_taco.py
"""

import re
import sys
from itertools import combinations

from pypdf import PdfReader

from teste_personal.config import TACO_PDF, TACO_TXT

FONTE = "TACO 4ª ed. revisada e ampliada (NEPA/UNICAMP, 2011)"
COLUNAS = ["umidade", "kcal", "kj", "proteina", "lipideos", "colesterol", "carboidrato", "fibra", "cinzas", "calcio", "magnesio"]
VALOR = re.compile(r"^(\d+(,\d+)?|NA|Tr|\*)$")
INICIO_LINHA = re.compile(r"^(\d{1,3})\s+(\S.*)$")
CODIGOS = {"Tr": "traços", "NA": "não aplicável", "*": "não analisado", "": "não informado"}
CORRECOES_GRUPO = {"Miscelânea s": "Miscelâneas"}


def _num(v: str) -> float | None:
    if re.fullmatch(r"\d+(,\d+)?", v):
        return float(v.replace(",", "."))
    return None


def _valido(vals: list[str]) -> bool:
    """Checa kJ ≈ kcal x 4,184 e se umidade+proteína+lipídeos+carboidrato+cinzas ≈ 100 g
    (na TACO o carboidrato é calculado por diferença), para pegar colunas deslocadas na extração."""
    d = dict(zip(COLUNAS, vals))
    kcal, kj = _num(d["kcal"]), _num(d["kj"])
    if kcal is None or kj is None or abs(kj - kcal * 4.184) > max(4, kj * 0.015):
        return False
    partes = [d[c] for c in ("umidade", "proteina", "lipideos", "carboidrato", "cinzas")]
    if "*" in partes:
        return False
    return abs(sum(_num(p) or 0.0 for p in partes) - 100) <= 5  # Tr, NA e célula vazia contam como zero


def _com_celulas_vazias(texto: str, n_descricao: int) -> list[str]:
    """Célula vazia no PDF vira espaço duplo no texto extraído; colunas faltando no fim viram vazias."""
    pecas = texto.strip().split(" ")
    i = vistos = 0
    while vistos < n_descricao:
        vistos += bool(pecas[i])
        i += 1
    vals = pecas[i:]
    while vals and not vals[0]:
        vals.pop(0)
    return vals + [""] * (len(COLUNAS) - len(vals)) if len(vals) <= len(COLUNAS) else []


def _separar(texto: str) -> tuple[str, list[str]] | None:
    # Decimal partido pelo pypdf: "65 ,7" / "69, 8" -> "65,7" / "69,8" (valores nunca começam ou terminam em vírgula).
    texto = re.sub(r"(\d) ?, (\d)|(\d) ,(\d)", lambda m: f"{m[1] or m[3]},{m[2] or m[4]}", texto)
    tokens = texto.split()
    n = len(tokens)
    while n > 0 and VALOR.match(tokens[n - 1]):
        n -= 1
    descricao, vals = " ".join(tokens[:n]), tokens[n:]
    if len(vals) == len(COLUNAS):
        return (descricao, vals) if _valido(vals) else None
    if len(vals) < len(COLUNAS):
        vals = _com_celulas_vazias(texto, n)
        return (descricao, vals) if vals and _valido(vals) else None
    # O pypdf às vezes quebra um número em dois ("19 74" -> 1974, "5 5,2" -> 55,2): tenta reunir pares.
    excesso = len(vals) - len(COLUNAS)
    if excesso <= 2:
        inteiros = [
            i for i in range(len(vals) - 1) if vals[i].isdigit() and re.fullmatch(r"\d+(,\d+)?", vals[i + 1])
        ]
        for pares in combinations(inteiros, excesso):
            if any(b - a < 2 for a, b in zip(pares, pares[1:])):
                continue
            unidos, pular = [], set()
            for i, v in enumerate(vals):
                if i in pular:
                    continue
                if i in pares:
                    unidos.append(v + vals[i + 1])
                    pular.add(i + 1)
                else:
                    unidos.append(v)
            if _valido(unidos):
                return descricao, unidos
    return None


def _formatar(numero: str, descricao: str, grupo: str, vals: list[str]) -> str:
    d = dict(zip(COLUNAS, vals))

    def g(chave: str, unidade: str) -> str:
        v = d[chave]
        return CODIGOS[v] if v in CODIGOS else f"{v} {unidade}"

    return (
        f"TACO nº {numero} — {descricao} (grupo: {grupo}). Por 100 g de parte comestível: "
        f"energia {g('kcal', 'kcal')}; proteína {g('proteina', 'g')}; lipídeos {g('lipideos', 'g')}; "
        f"carboidrato {g('carboidrato', 'g')}; fibra alimentar {g('fibra', 'g')}; colesterol {g('colesterol', 'mg')}; "
        f"umidade {g('umidade', '%')}. Fonte: {FONTE}."
    )


def extrair() -> tuple[list[str], list[str]]:
    linhas_saida, excluidos = [], []
    grupo = "não identificado"
    for pagina in PdfReader(TACO_PDF).pages:
        texto = pagina.extract_text() or ""
        if not ("Tabela 1" in texto and "Umidade" in texto and "(kcal)" in texto):
            continue
        linhas = texto.splitlines()
        inicio = next((i for i, l in enumerate(linhas) if "Descrição dos alimentos" in l), None)
        if inicio is None:
            continue
        pendente: list[str] | None = None  # [numero, texto acumulado]

        def fechar() -> None:
            nonlocal pendente
            if pendente is None:
                return
            resultado = _separar(pendente[1])
            if resultado:
                linhas_saida.append(_formatar(pendente[0], resultado[0], grupo, resultado[1]))
            else:
                excluidos.append(f"nº {pendente[0]}: {pendente[1]}")
            pendente = None

        for linha in linhas[inicio + 1 :]:
            linha = linha.strip()
            if not linha:
                continue
            m = INICIO_LINHA.match(linha)
            if m:
                fechar()
                pendente = [m.group(1), m.group(2)]
            elif pendente is not None and not VALOR.match(pendente[1].split()[-1]):
                pendente[1] += " " + linha  # descrição quebrada em duas linhas
            else:
                fechar()
                if not any(ch.isdigit() for ch in linha):
                    grupo = " ".join(linha.split())
                    grupo = CORRECOES_GRUPO.get(grupo, grupo)
                    if grupo.count("(") > grupo.count(")"):
                        grupo += ")"
        fechar()
    return linhas_saida, excluidos


def main() -> None:
    linhas, excluidos = extrair()
    cabecalho = (
        f"Tabela Brasileira de Composição de Alimentos — {FONTE}. Composição centesimal por 100 g de parte comestível. "
        "Legenda: 'traços' = valor abaixo do limite de quantificação; 'não aplicável' = nutriente não aplicável ao alimento; "
        "'não analisado' = análise não realizada."
    )
    TACO_TXT.write_text("\n".join([cabecalho, *linhas]) + "\n", encoding="utf-8")
    print(f"{len(linhas)} alimentos gravados em {TACO_TXT.name}")
    if excluidos:
        print(f"{len(excluidos)} linhas excluídas por falharem na validação:", *excluidos, sep="\n  ", file=sys.stderr)


if __name__ == "__main__":
    main()

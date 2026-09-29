import re
import unicodedata
from functools import cache

from teste_personal.config import TACO_TXT

IGNORAR = {"de", "da", "do", "das", "dos", "e", "em", "a", "o", "com"}


def _termos(texto: str) -> list[str]:
    sem_acento = unicodedata.normalize("NFKD", texto.lower()).encode("ascii", "ignore").decode()
    return [t for t in re.findall(r"[a-z0-9]+", sem_acento) if t not in IGNORAR]


def _casa(termo: str, termos_alimento: list[str]) -> bool:
    # Aceita plural/variação simples: "ovos" ~ "ovo", "cozida" ~ "cozido".
    return any(t == termo or (len(t) >= 4 and len(termo) >= 4 and t[:-1] == termo[:-1]) for t in termos_alimento)


@cache
def _tabela() -> list[tuple[list[str], str]]:
    linhas = TACO_TXT.read_text(encoding="utf-8").splitlines()[1:]
    return [(_termos(re.search(r"— (.*?) \(grupo:", l).group(1)), l) for l in linhas]


def consultar_taco(alimentos: list[str]) -> str:
    """Consulta a composição nutricional (por 100 g) de alimentos na tabela TACO local
    (Tabela Brasileira de Composição de Alimentos, NEPA/UNICAMP). Use ANTES da pesquisa na Web
    para valores de alimentos. Aceita vários alimentos de uma vez.

    Retorna, para cada alimento pedido, até 5 itens da TACO mais parecidos, com o número TACO e os valores.
    Escolha o item que corresponde ao preparo certo (cru, cozido, grelhado...). Se nenhum corresponder,
    diga que o alimento não está na TACO — não adapte valores de outro item.

    Args:
        alimentos: Nomes dos alimentos com o preparo, ex.: ["arroz branco cozido", "peito de frango grelhado", "banana prata"].
    """
    respostas = []
    for pedido in alimentos:
        termos = _termos(pedido.replace("-", " "))
        if not termos:
            continue
        pontuados = []
        for termos_alimento, linha in _tabela():
            acertos = sum(_casa(t, termos_alimento) for t in termos)
            if acertos:
                pontuados.append((acertos / len(termos), -len(termos_alimento), linha))
        pontuados.sort(reverse=True)
        melhores = [linha for nota, _, linha in pontuados[:5] if nota >= 0.5]
        if melhores:
            respostas.append(f"## {pedido}\n" + "\n".join(f"- {l}" for l in melhores))
        else:
            respostas.append(f"## {pedido}\nNão encontrado na TACO.")
    return "\n\n".join(respostas)

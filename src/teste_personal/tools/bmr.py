from typing import Literal

FATORES_ATIVIDADE = {
    "sedentario": 1.2,
    "leve": 1.375,
    "moderado": 1.55,
    "intenso": 1.725,
    "muito_intenso": 1.9,
}


def calcular_taxa_metabolica_basal(
    sexo: Literal["masculino", "feminino"],
    peso_kg: float,
    altura_cm: float,
    idade_anos: int,
    nivel_atividade: Literal["sedentario", "leve", "moderado", "intenso", "muito_intenso"],
) -> dict:
    """Calcula a Taxa Metabólica Basal (TMB) pela fórmula de Harris-Benedict revisada
    (Roza & Shizgal, 1984) e o Gasto Energético Total (GET = TMB x fator de atividade).
    Use SEMPRE esta ferramenta para TMB/GET; nunca estime esses valores.

    Fatores de atividade: sedentario=1.2 (pouco ou nenhum exercício), leve=1.375 (1-3x/semana),
    moderado=1.55 (3-5x/semana), intenso=1.725 (6-7x/semana), muito_intenso=1.9 (treino 2x/dia ou trabalho físico pesado).

    Args:
        sexo: "masculino" ou "feminino".
        peso_kg: Peso corporal em quilogramas.
        altura_cm: Altura em centímetros.
        idade_anos: Idade em anos completos.
        nivel_atividade: Um de sedentario, leve, moderado, intenso, muito_intenso.
    """
    if not 20 <= peso_kg <= 400:
        raise ValueError(f"peso_kg fora da faixa válida (20-400): {peso_kg}")
    if not 100 <= altura_cm <= 250:
        raise ValueError(f"altura_cm fora da faixa válida (100-250): {altura_cm}")
    if not 10 <= idade_anos <= 120:
        raise ValueError(f"idade_anos fora da faixa válida (10-120): {idade_anos}")
    if nivel_atividade not in FATORES_ATIVIDADE:
        raise ValueError(f"nivel_atividade inválido: {nivel_atividade}. Use um de {list(FATORES_ATIVIDADE)}")

    if sexo == "masculino":
        tmb = 88.362 + 13.397 * peso_kg + 4.799 * altura_cm - 5.677 * idade_anos
        formula = "TMB = 88,362 + (13,397 x peso) + (4,799 x altura) - (5,677 x idade)"
    elif sexo == "feminino":
        tmb = 447.593 + 9.247 * peso_kg + 3.098 * altura_cm - 4.330 * idade_anos
        formula = "TMB = 447,593 + (9,247 x peso) + (3,098 x altura) - (4,330 x idade)"
    else:
        raise ValueError(f"sexo inválido: {sexo}. Use 'masculino' ou 'feminino'.")

    fator = FATORES_ATIVIDADE[nivel_atividade]
    return {
        "metodo": "Harris-Benedict revisada (Roza & Shizgal, 1984)",
        "formula_tmb": formula,
        "entradas": {
            "sexo": sexo,
            "peso_kg": peso_kg,
            "altura_cm": altura_cm,
            "idade_anos": idade_anos,
            "nivel_atividade": nivel_atividade,
            "fator_atividade": fator,
        },
        "tmb_kcal": round(tmb, 1),
        "get_kcal": round(tmb * fator, 1),
    }

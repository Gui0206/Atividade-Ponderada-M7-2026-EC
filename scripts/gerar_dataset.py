"""Gera dados FICTÍCIOS de USD/BRL para a atividade, sem fontes de mercado.

Execute na raiz: python3 scripts/gerar_dataset.py
Usa apenas a biblioteca padrão. Os parâmetros abaixo são escolhas didáticas.
"""

import csv
import json
import math
import random
from datetime import date, timedelta
from pathlib import Path


def main():
    seed = 2026
    rng = random.Random(seed)
    inicio, fim = date(2023, 1, 2), date(2025, 12, 31)
    linhas = []
    dia = inicio
    preco = 5.20
    retorno_anterior = 0.0
    while dia <= fim:
        if dia.weekday() < 5:
            i = len(linhas)
            # Variações sintéticas: tendência lenta, ruído e persistência fraca.
            referencia = 5.20 + 0.35 * math.sin(2 * math.pi * i / 400)
            retorno = (
                0.02 * math.log(referencia / preco)
                + 0.10 * retorno_anterior
                + rng.gauss(0, 0.006)
            )
            preco *= math.exp(retorno)
            linhas.append((dia.isoformat(), f"{preco:.4f}"))
            retorno_anterior = retorno
        dia += timedelta(days=1)

    destino = Path(__file__).resolve().parents[1] / "data"
    destino.mkdir(parents=True, exist_ok=True)
    arquivo = destino / "dolar_brl_sintetico.csv"
    with arquivo.open("w", encoding="utf-8", newline="") as f:
        escritor = csv.writer(f)
        escritor.writerow(["data", "fechamento"])
        escritor.writerows(linhas)

    metadados = {
        "arquivo": arquivo.name,
        "natureza": "Dados sintéticos; não são cotações históricas reais.",
        "origem": "Script Python elaborado com auxílio de LLM, sem consulta a mercado.",
        "par": "USD/BRL",
        "unidade": "Reais brasileiros por 1 dólar americano",
        "inicio": linhas[0][0],
        "fim": linhas[-1][0],
        "registros": len(linhas),
        "frequencia": "Segunda a sexta; feriados não são excluídos.",
        "formato": "UTF-8, separador vírgula, decimal ponto, data ISO 8601",
        "colunas": {"data": "Data da observação", "fechamento": "Cotação de fechamento fictícia em BRL/USD"},
        "seed": seed,
        "parametros": {"preco_inicial": 5.20, "amplitude_referencia": 0.35, "periodo_observacoes": 400,
                       "reversao_media": 0.02, "persistencia_retorno": 0.10, "desvio_ruido": 0.006},
        "horizonte_proposto": "Fechamento da próxima linha: próximo dia de segunda a sexta, inclusive feriados.",
        "treinamento_proposto": "Usar os últimos 5 fechamentos conhecidos para prever o seguinte; separar treino e teste cronologicamente, sem embaralhar.",
        "limitacao": "Série artificial para demonstrar a integração; não serve para validar previsões financeiras reais."
    }
    (destino / "dolar_brl_sintetico.metadata.json").write_text(
        json.dumps(metadados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Gerado: {arquivo} ({len(linhas)} registros)")


if __name__ == "__main__":
    main()

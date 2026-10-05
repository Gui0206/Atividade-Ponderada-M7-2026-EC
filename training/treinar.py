"""Treina e exporta uma regressão linear para a série sintética USD/BRL."""

import csv
import hashlib
import json
import platform
from datetime import date
from pathlib import Path

import joblib
import numpy as np
import sklearn
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error


def main():
    csv_path = Path("data/dolar_brl_sintetico.csv")
    destino = Path("artifacts")
    janela = 5

    with csv_path.open(encoding="utf-8", newline="") as arquivo:
        leitor = csv.DictReader(arquivo)
        if leitor.fieldnames != ["data", "fechamento"]:
            raise ValueError("O CSV precisa das colunas data e fechamento, nessa ordem.")
        linhas = list(leitor)

    datas = [date.fromisoformat(linha["data"]) for linha in linhas]
    precos = np.array([float(linha["fechamento"]) for linha in linhas])
    if len(precos) < 20 or not np.isfinite(precos).all() or (precos <= 0).any():
        raise ValueError("São necessários pelo menos 20 preços válidos e positivos.")
    if any(anterior >= atual for anterior, atual in zip(datas, datas[1:])):
        raise ValueError("As datas precisam estar em ordem crescente, sem duplicatas.")

    # Cada entrada contém somente preços anteriores ao valor que será previsto.
    X = np.array([precos[i - janela:i] for i in range(janela, len(precos))])
    y = precos[janela:]
    datas_alvo = datas[janela:]
    corte = int(len(X) * 0.8)
    X_treino, X_teste = X[:corte], X[corte:]
    y_treino, y_teste = y[:corte], y[corte:]

    modelo = LinearRegression()
    modelo.fit(X_treino, y_treino)
    previsoes = modelo.predict(X_teste)
    # Referência simples: prever que o próximo preço será igual ao último.
    baseline = X_teste[:, -1]

    relatorio = {
        "modelo": "LinearRegression",
        "dataset": str(csv_path),
        "sha256_dataset": hashlib.sha256(csv_path.read_bytes()).hexdigest(),
        "dados_sinteticos": True,
        "janela": janela,
        "registros_csv": len(precos),
        "amostras_treino": len(X_treino),
        "amostras_teste": len(X_teste),
        "periodo_alvos_treino": [datas_alvo[0].isoformat(), datas_alvo[corte - 1].isoformat()],
        "periodo_alvos_teste": [datas_alvo[corte].isoformat(), datas_alvo[-1].isoformat()],
        "avaliacao": "Próxima observação, usando os 5 fechamentos reais anteriores; sem embaralhar.",
        "mae_brl": float(mean_absolute_error(y_teste, previsoes)),
        "rmse_brl": float(np.sqrt(mean_squared_error(y_teste, previsoes))),
        "mae_baseline_brl": float(mean_absolute_error(y_teste, baseline)),
        "versoes": {"python": platform.python_version(), "scikit_learn": sklearn.__version__,
                    "numpy": np.__version__, "joblib": joblib.__version__},
    }

    destino.mkdir(parents=True, exist_ok=True)
    artefato = {
        "modelo": modelo,
        "janela": janela,
        "ordem_entradas": "Do fechamento mais antigo ao mais recente",
        "par": "USD/BRL",
        "horizonte": "Próxima observação da série (segunda a sexta, incluindo feriados)",
        "versoes": relatorio["versoes"],
    }
    caminho_modelo = destino / "modelo.joblib"
    joblib.dump(artefato, caminho_modelo)

    # Confere se o arquivo salvo pode ser carregado e mantém as mesmas previsões.
    carregado = joblib.load(caminho_modelo)
    np.testing.assert_allclose(carregado["modelo"].predict(X_teste), previsoes)
    relatorio["recarga_validada"] = True

    with (destino / "previsoes_teste.csv").open("w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.writer(arquivo)
        escritor.writerow(["data", "real", "previsao", "baseline"])
        for dia, real, previsto, referencia in zip(datas_alvo[corte:], y_teste, previsoes, baseline):
            escritor.writerow([dia.isoformat(), f"{real:.4f}", f"{previsto:.4f}", f"{referencia:.4f}"])

    (destino / "metricas.json").write_text(
        json.dumps(relatorio, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(relatorio, ensure_ascii=False, indent=2))
    print(f"Modelo exportado e recarregado com sucesso: {caminho_modelo}")


if __name__ == "__main__":
    main()

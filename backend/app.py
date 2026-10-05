"""API para consultar o modelo de dólar treinado, usando o terminal."""

import math
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

import joblib
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field


@asynccontextmanager
async def lifespan(app: FastAPI):
    caminho = Path("/app/artifacts/modelo.joblib")
    if not caminho.is_file():
        raise RuntimeError("Modelo não encontrado. Execute o treinamento e monte a pasta artifacts.")
    artefato = joblib.load(caminho)
    if artefato["janela"] != 5 or artefato["modelo"].n_features_in_ != 5:
        raise RuntimeError("O modelo precisa receber exatamente 5 fechamentos.")
    app.state.artefato = artefato
    yield


app = FastAPI(title="Previsão do dólar", lifespan=lifespan, docs_url=None, redoc_url=None)

Preco = Annotated[float, Field(gt=0, allow_inf_nan=False, strict=True)]


class Entrada(BaseModel):
    model_config = ConfigDict(extra="forbid")
    precos: list[Preco] = Field(
        min_length=5, max_length=5,
        description="Últimos 5 fechamentos em reais, do mais antigo ao mais recente.",
    )


@app.get("/health")
def health():
    return {"status": "ok", "modelo_carregado": True}


@app.post("/predict")
def predict(entrada: Entrada):
    artefato = app.state.artefato
    previsao = float(artefato["modelo"].predict([entrada.precos])[0])
    if not math.isfinite(previsao) or previsao <= 0:
        raise HTTPException(status_code=422, detail="Esses preços geraram uma previsão inválida.")
    return {
        "par": artefato["par"],
        "previsao": round(previsao, 4),
        "unidade": "BRL por USD",
        "horizonte": artefato["horizonte"],
    }

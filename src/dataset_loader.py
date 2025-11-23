"""
dataset_loader.py
------------------
Carrega, normaliza e padroniza datasets adversariais e benignos para o pipeline AETHON.

Origem dos datasets (conforme arquivos enviados pelo autor):
- hf_prompt-injections_train.parquet   (HuggingFace - Prompt Injection Dataset)
- hf_prompt-injections_test.parquet    (HuggingFace - Prompt Injection Dataset)
- hf_red_team_attempts.jsonl           (HuggingFace - Red Team Attempts / RLHF style)
- kaggle_red_team_prompts.json         (Kaggle - Red Teaming Prompts Collection)

Todos os arquivos estão no diretório:
    /home/leonardo/Documentos/aethon_repo/datasets/

Este módulo fornece:
- load_dataset(name)
- normalize_dataframe(df)
- map_columns(df)
"""

import json
import pandas as pd
from pathlib import Path


DATA_DIR = Path("/home/leonardo/Documentos/aethon_repo/datasets")


# ------------------------------------------------------------
# 1) Função principal de carregamento
# ------------------------------------------------------------
def load_dataset(name: str) -> pd.DataFrame:
    """
    Carrega um dataset pelo nome padrão do projeto.
    O nome deve corresponder a um dos seguintes casos:

    - "prompt_injections_train"
    - "prompt_injections_test"
    - "red_team_attempts"
    - "kaggle_redteam"
    """
    path = None

    if name == "prompt_injections_train":
        path = DATA_DIR / "hf_prompt-injections_train.parquet"

    elif name == "prompt_injections_test":
        path = DATA_DIR / "hf_prompt-injections_test.parquet"

    elif name == "red_team_attempts":
        path = DATA_DIR / "hf_red_team_attempts.jsonl"

    elif name == "kaggle_redteam":
        path = DATA_DIR / "kaggle_red_team_prompts.json"

    else:
        raise ValueError(f"[ERRO] Dataset '{name}' não reconhecido.")

    if not path.exists():
        raise FileNotFoundError(f"[ERRO] Caminho não encontrado: {path}")

    print(f"[LOAD] Carregando dataset: {path}")

    # --- parquet ---
    if path.suffix == ".parquet":
        df = pd.read_parquet(path)
        return normalize_dataframe(df, source=name)

    # --- jsonl ---
    if path.suffix == ".jsonl":
        df = pd.read_json(path, lines=True)
        return normalize_dataframe(df, source=name)

    # --- json ---
    if path.suffix == ".json":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        df = pd.DataFrame(data)
        return normalize_dataframe(df, source=name)

    raise ValueError(f"[ERRO] Tipo de arquivo não suportado: {path}")
    

# ------------------------------------------------------------
# 2) Normalização de dataframes
# ------------------------------------------------------------
def normalize_dataframe(df: pd.DataFrame, source: str) -> pd.DataFrame:
    """
    Normaliza dataframes vindos de diferentes formatos/origens.
    Cria colunas padronizadas:
        - prompt_id
        - prompt_text
        - label (0 = benigno, 1 = adversarial)
        - source
    """

    df = df.copy()
    df["source"] = source

    # mapeamento heurístico com base nas colunas encontradas
    df = map_columns(df)

    # remover linhas inválidas
    df = df.dropna(subset=["prompt_text"])
    df = df.reset_index(drop=True)

    print(f"[NORMALIZE] '{source}' → shape={df.shape}")
    return df


# ------------------------------------------------------------
# 3) Mapeamento automático de colunas
# ------------------------------------------------------------
def map_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Detecta automaticamente as colunas relevantes para o prompt.
    Este método foi criado após análise dos arquivos enviados
    e cobre todos os formatos atuais.
    """

    # compatibilidade parquet (HuggingFace Prompt Injections)
    if "text" in df.columns:
        df["prompt_text"] = df["text"]

    if "prompt" in df.columns:
        df["prompt_text"] = df["prompt"]

    # compatibilidade Kaggle red-team
    if "prompt_text" not in df.columns and "prompt" in df.columns:
        df["prompt_text"] = df["prompt"]

    # alguns arquivos têm "id", outros não
    if "id" in df.columns:
        df["prompt_id"] = df["id"].astype(str)
    else:
        df["prompt_id"] = df.index.astype(str)

    # criar coluna de rótulo (se não existir)
    if "label" not in df.columns:
        # Se o dataset não tiver label, consideramos ADVERSARIAL
        df["label"] = 1
    else:
        # garantir formatação binária
        df["label"] = df["label"].astype(int).clip(0, 1)

    return df[["prompt_id", "prompt_text", "label", "source"]]

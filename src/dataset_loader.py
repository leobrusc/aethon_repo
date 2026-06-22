"""
dataset_loader.py
-----------------
Carrega, normaliza e padroniza datasets adversariais e benignos para o
pipeline AETHON.

Datasets canonicos:
- prompt_injections_train
- prompt_injections_test
- red_team_attempts
- kaggle_redteam

Tambem aceita "all" ou "all_datasets" para concatenar todos os datasets
canonicos sem incluir backups locais ou copias auxiliares.
"""

from pathlib import Path
import json
import hashlib

import pandas as pd
from loaders import SOURCE_NORMALIZERS


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "datasets"

DATASET_FILES = {
    "prompt_injections_train": "hf_prompt-injections_train.parquet",
    "prompt_injections_test": "hf_prompt-injections_test.parquet",
    "red_team_attempts": "hf_red_team_attempts.jsonl",
    "kaggle_redteam": "kaggle_red_team_prompts.json",
    "advbench_harmful": "advbench_harmful_behaviors.csv",
    "jailbreakbench_behaviors": "jailbreakbench_behaviors.jsonl",
    "wildjailbreak_eval": "wildjailbreak_eval.jsonl",
    "prompt_injection_core": "neuralchemy_prompt_injection_core.jsonl",
    "notinject": "notinject.jsonl",
    "cyberseceval_prompt_injection": "cyberseceval_prompt_injection.json",
}

ALL_DATASETS = tuple(DATASET_FILES.keys())


def get_dataset_path(name: str) -> Path:
    if name not in DATASET_FILES:
        raise ValueError(f"[ERRO] Dataset '{name}' nao reconhecido.")
    return DATA_DIR / DATASET_FILES[name]


def get_dataset_metadata(name: str) -> dict:
    """Return source-file metadata used in reproducible benchmark manifests."""
    if name in {"all", "all_datasets"}:
        return {
            "name": name,
            "members": [get_dataset_metadata(member) for member in ALL_DATASETS],
        }
    path = get_dataset_path(name)
    digest = hashlib.sha256()
    with path.open("rb") as dataset_file:
        for chunk in iter(lambda: dataset_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return {
        "name": name,
        "file": path.name,
        "sha256": digest.hexdigest(),
        "bytes": path.stat().st_size,
    }


def load_dataset(name: str) -> pd.DataFrame:
    """
    Carrega um dataset pelo nome padrao do projeto.

    Retorna sempre as colunas:
    - prompt_id
    - prompt_text
    - label (0 = benigno, 1 = adversarial)
    - source
    """
    if name in {"all", "all_datasets"}:
        frames = [load_dataset(dataset_name) for dataset_name in ALL_DATASETS]
        df = pd.concat(frames, ignore_index=True)
        print(f"[LOAD] Todos os datasets combinados -> shape={df.shape}")
        return df

    if name not in DATASET_FILES:
        available = list(DATASET_FILES.keys()) + ["all", "all_datasets"]
        raise ValueError(f"[ERRO] Dataset '{name}' nao reconhecido. Disponiveis: {available}")

    path = get_dataset_path(name)
    if not path.exists():
        raise FileNotFoundError(f"[ERRO] Caminho nao encontrado: {path}")

    print(f"[LOAD] Carregando dataset: {path}")

    if path.suffix == ".parquet":
        df = pd.read_parquet(path)
    elif path.suffix == ".csv":
        df = pd.read_csv(path)
    elif path.suffix in {".json", ".jsonl"}:
        df = read_json_or_jsonl(path)
    else:
        raise ValueError(f"[ERRO] Tipo de arquivo nao suportado: {path}")

    return normalize_dataframe(df, source=name)


def read_json_or_jsonl(path: Path) -> pd.DataFrame:
    """
    Le JSONL verdadeiro ou JSON array.

    O dataset oficial Anthropic red-team-attempts e publicado como .jsonl.gz,
    mas o conteudo descompactado e um array JSON, nao JSON por linha.
    """
    with path.open("r", encoding="utf-8") as f:
        first_char = ""
        while not first_char:
            char = f.read(1)
            if not char:
                raise ValueError(f"[ERRO] Arquivo JSON vazio: {path}")
            first_char = char.strip()

    if path.suffix == ".jsonl" and first_char != "[":
        return pd.read_json(path, lines=True)

    if first_char in {"[", "{"}:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            return pd.DataFrame(data)
        if isinstance(data, dict):
            if all(isinstance(value, dict) for value in data.values()):
                return pd.DataFrame(data)
            return pd.DataFrame([data])

        raise ValueError(f"[ERRO] Estrutura JSON nao suportada em: {path}")

    return pd.read_json(path, lines=True)


def normalize_dataframe(df: pd.DataFrame, source: str) -> pd.DataFrame:
    """
    Normaliza dataframes vindos de diferentes formatos/origens.
    """
    df = df.copy()
    if source in SOURCE_NORMALIZERS:
        normalized = SOURCE_NORMALIZERS[source](df)
        normalized["source"] = source
        normalized = normalized.dropna(subset=["prompt_text"]).reset_index(drop=True)
        print(f"[NORMALIZE] '{source}' -> shape={normalized.shape}")
        return normalized[["prompt_id", "prompt_text", "label", "source"]]

    df["source"] = source
    df = map_columns(df, source=source)
    df = df.dropna(subset=["prompt_text"])
    df["prompt_text"] = df["prompt_text"].astype(str)
    df = df[df["prompt_text"].str.len() > 0]
    df = df.reset_index(drop=True)

    print(f"[NORMALIZE] '{source}' -> shape={df.shape}")
    return df


def map_columns(df: pd.DataFrame, source: str) -> pd.DataFrame:
    """
    Detecta automaticamente as colunas relevantes para o prompt.
    Cobre os formatos atuais do repositorio.
    """
    if source == "cyberseceval_prompt_injection" and {"test_case_prompt", "user_input"}.issubset(df.columns):
        df["prompt_text"] = df["test_case_prompt"].astype(str) + "\n\n" + df["user_input"].astype(str)

    prompt_candidates = [
        "prompt_text",
        "text",
        "prompt",
        "user_input",
        "test_case_prompt",
        "transcript",
        "task_description",
        "goal",
        "Goal",
        "Behavior",
        "instruction",
        "query",
    ]
    for col in prompt_candidates:
        if col in df.columns:
            df["prompt_text"] = df[col]
            break

    if "prompt_text" not in df.columns:
        raise ValueError(f"[ERRO] Nenhuma coluna de prompt encontrada. Colunas: {list(df.columns)}")

    if "id" in df.columns:
        df["prompt_id"] = df["id"].astype(str)
    else:
        df["prompt_id"] = df.index.astype(str)

    if source == "notinject":
        df["label"] = 0
    elif source == "cyberseceval_prompt_injection":
        df["label"] = 1
    elif "label" in df.columns:
        df["label"] = normalize_label_series(df["label"])
    elif "answer" in df.columns:
        df["label"] = normalize_label_series(df["answer"])
    elif "split" in df.columns:
        df["label"] = normalize_label_series(df["split"])
    else:
        # Red-team datasets sem label binario sao tratados como adversariais.
        df["label"] = 1

    return df[["prompt_id", "prompt_text", "label", "source"]]


def normalize_label_series(series: pd.Series) -> pd.Series:
    """
    Converte labels numericos ou textuais para binario.
    Textos contendo benign/safe viram 0; harmful/adversarial/jailbreak/malicious viram 1.
    """
    if pd.api.types.is_numeric_dtype(series):
        return series.astype(int).clip(0, 1)

    labels = series.astype(str).str.lower()
    mapped = pd.Series(1, index=series.index)
    mapped[labels.str.contains("harmful|adversarial|jailbreak|malicious|attack", regex=True, na=False)] = 1
    mapped[labels.str.contains("benign|safe|harmless", regex=True, na=False)] = 0
    return mapped.astype(int)

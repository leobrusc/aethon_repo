"""Phase 1.5 error analysis for the fixed, detection-only AETHON results."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

from aethon_heuristic import PATTERNS
from benchmark.detection import EVALUATION_DATASETS, LABEL_PROVENANCE
from dataset_loader import load_dataset


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PHASE1 = PROJECT_ROOT / "results" / "revision" / "detection" / "per_prompt_results.csv"
DEFAULT_MODEL = PROJECT_ROOT / "src" / "models" / "aethon_tfidf_lr_revision.pkl"
DEFAULT_OUTPUT = PROJECT_ROOT / "results" / "revision" / "error_analysis"
THRESHOLDS = tuple(i / 10 for i in range(1, 10))
TRIGGER_TERMS = ("ignore", "system", "instructions", "prompt", "jailbreak", "role", "assistant", "developer", "security", "attack")
SAFETY_TERMS = ("safe", "safety", "ethical", "harmless", "avoid", "refuse", "policy", "guideline", "sensitive")
MISSED_CATEGORIES = {
    "instruction_override": r"ignore|disregard|override|instruction|system prompt|do not follow|forget",
    "role_manipulation": r"role[- ]?play|pretend|act as|you are|persona|character",
    "jailbreak_framing": r"jailbreak|DAN\b|developer mode|uncensored|no restrictions|bypass",
    "encoding_obfuscation": r"base64|rot13|encode|decode|cipher|unicode|hexadecimal|leet|obfuscat",
    "semantic_reformulation": r"hypothetical|fiction|novel|research|educational|simulation|thought experiment",
    "indirect_injection": r"document|webpage|email|quoted text|retrieved|tool output|external content",
}


def normalized_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", str(text)).lower()
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _write_table(frame: pd.DataFrame, path: Path, markdown: bool = False) -> None:
    frame.to_csv(path, index=False)
    if markdown:
        display = frame.fillna("NA").astype(str)
        header = "| " + " | ".join(display.columns) + " |\n"
        divider = "| " + " | ".join("---" for _ in display.columns) + " |\n"
        rows = "".join("| " + " | ".join(row) + " |\n" for row in display.to_numpy())
        path.with_suffix(".md").write_text(header + divider + rows, encoding="utf-8")


def load_evaluation_prompts(datasets=EVALUATION_DATASETS) -> pd.DataFrame:
    frames = []
    for dataset in datasets:
        frame = load_dataset(dataset).rename(columns={"label": "true_label"})
        frame["dataset"] = dataset
        frame["prompt_id"] = frame["prompt_id"].astype(str)
        frames.append(frame[["dataset", "prompt_id", "prompt_text", "true_label"]])
    return pd.concat(frames, ignore_index=True)


def error_frames(results: pd.DataFrame, prompts: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    selected = results[results["condition"].isin(["B2", "B3"])].copy()
    keys = ["dataset", "prompt_id"]
    selected["prompt_id"] = selected["prompt_id"].astype(str)
    selected["_occurrence"] = selected.groupby(keys + ["condition"]).cumcount()
    prompt_lookup = prompts.copy()
    prompt_lookup["_occurrence"] = prompt_lookup.groupby(keys).cumcount()
    merged = selected.merge(prompt_lookup, on=keys + ["_occurrence"], how="left", validate="many_to_one")
    if merged["prompt_text"].isna().any():
        raise ValueError("Could not recover diagnostic text for every Phase 1 row")
    recovered_hash = merged["prompt_text"].map(lambda text: hashlib.sha256(text.encode("utf-8")).hexdigest())
    if not recovered_hash.equals(merged["prompt_sha256"]):
        raise ValueError("Recovered diagnostic text does not match Phase 1 prompt hashes")
    public_columns = [
        "dataset", "prompt_id", "prompt_sha256", "true_label_x", "condition", "ml_score",
        "heuristic_prediction", "ml_prediction", "final_prediction", "label_provenance",
    ]
    public = merged.rename(columns={"true_label_x": "true_label"})
    public_columns[3] = "true_label"
    false_positives = public[(public.true_label == 0) & (public.final_prediction == 1)][public_columns].copy()
    false_negatives = public[(public.true_label == 1) & (public.final_prediction == 0)][public_columns].copy()
    private = public[(public.true_label == 0) & (public.final_prediction == 1)][public_columns + ["prompt_text"]].copy()
    return false_positives, false_negatives, private


def heuristic_rule_coverage(prompts: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    adversarial_total = int((prompts.true_label == 1).sum())
    rows = []
    for index, pattern in enumerate(PATTERNS, start=1):
        diagnostic_pattern = re.sub(r"\((?!\?)", "(?:", pattern)
        matched = prompts.prompt_text.str.contains(diagnostic_pattern, case=False, regex=True, na=False)
        tp = int((matched & (prompts.true_label == 1)).sum())
        fp = int((matched & (prompts.true_label == 0)).sum())
        rows.append({
            "rule_id": f"H{index}", "pattern": pattern, "matches": int(matched.sum()),
            "true_positives": tp, "false_positives": fp,
            "precision": tp / int(matched.sum()) if matched.any() else np.nan,
            "adversarial_coverage": tp / adversarial_total if adversarial_total else np.nan,
        })
    any_match = pd.Series(False, index=prompts.index)
    for pattern in PATTERNS:
        diagnostic_pattern = re.sub(r"\((?!\?)", "(?:", pattern)
        any_match |= prompts.prompt_text.str.contains(diagnostic_pattern, case=False, regex=True, na=False)
    missed = prompts[(prompts.true_label == 1) & ~any_match].copy()
    category_rows = []
    assigned = pd.Series(False, index=missed.index)
    for category, pattern in MISSED_CATEGORIES.items():
        matches = missed.prompt_text.str.contains(pattern, case=False, regex=True, na=False) & ~assigned
        category_rows.append({"category": category, "missed_attacks": int(matches.sum()), "share_of_all_missed": float(matches.sum() / len(missed)) if len(missed) else np.nan})
        assigned |= matches
    remaining = int((~assigned).sum())
    category_rows.append({"category": "other", "missed_attacks": remaining, "share_of_all_missed": remaining / len(missed) if len(missed) else np.nan})
    return pd.DataFrame(rows), pd.DataFrame(category_rows)


def lr_feature_analysis(model: Pipeline) -> tuple[pd.DataFrame, pd.DataFrame]:
    vectorizer = model.named_steps["tfidf"]
    classifier = model.named_steps["lr"]
    features = np.asarray(vectorizer.get_feature_names_out())
    coefficients = classifier.coef_[0]
    idf = vectorizer.idf_
    positive = np.argsort(coefficients)[-100:][::-1]
    negative = np.argsort(coefficients)[:100]
    rows = []
    for direction, indices in (("positive", positive), ("negative", negative)):
        for rank, feature_index in enumerate(indices, start=1):
            rows.append({"direction": direction, "rank": rank, "feature": features[feature_index], "coefficient": coefficients[feature_index], "coefficient_magnitude": abs(coefficients[feature_index]), "idf": idf[feature_index]})
    vocabulary = vectorizer.vocabulary_
    trigger_rows = []
    for term in TRIGGER_TERMS:
        feature_index = vocabulary.get(term)
        trigger_rows.append({
            "term": term, "in_vocabulary": feature_index is not None,
            "coefficient": coefficients[feature_index] if feature_index is not None else np.nan,
            "idf": idf[feature_index] if feature_index is not None else np.nan,
        })
    return pd.DataFrame(rows), pd.DataFrame(trigger_rows)


def distribution_shift(model: Pipeline, training: pd.DataFrame, prompts: pd.DataFrame, phase1_metrics: pd.DataFrame) -> pd.DataFrame:
    vectorizer = model.named_steps["tfidf"]
    analyzer = vectorizer.build_analyzer()
    train_matrix = vectorizer.transform(training.prompt_text)
    train_centroid = np.asarray(train_matrix.mean(axis=0)).ravel()
    train_norm = np.linalg.norm(train_centroid)
    vocab = set(vectorizer.vocabulary_)
    rows = []
    groups = [("prompt_injections_train", training.rename(columns={"label": "true_label"}))]
    groups.extend(prompts.groupby("dataset", sort=False))
    for dataset, frame in groups:
        matrix = vectorizer.transform(frame.prompt_text)
        centroid = np.asarray(matrix.mean(axis=0)).ravel()
        denominator = train_norm * np.linalg.norm(centroid)
        similarities = float(np.dot(train_centroid, centroid) / denominator) if denominator else np.nan
        token_lists = [analyzer(text) for text in frame.prompt_text]
        total_tokens = sum(len(tokens) for tokens in token_lists)
        known_tokens = sum(sum(token in vocab for token in tokens) for tokens in token_lists)
        lengths = frame.prompt_text.str.split().str.len()
        metric_row = phase1_metrics[(phase1_metrics.dataset == dataset) & (phase1_metrics.condition == "B2")]
        rows.append({
            "dataset": dataset, "rows": len(frame), "adversarial_prevalence": float(frame.true_label.mean()),
            "tfidf_centroid_cosine_to_training": similarities,
            "vocabulary_coverage": known_tokens / total_tokens if total_tokens else np.nan,
            "oov_rate": 1 - known_tokens / total_tokens if total_tokens else np.nan,
            "mean_words": float(lengths.mean()), "median_words": float(lengths.median()), "p95_words": float(lengths.quantile(.95)),
            "b2_f1": float(metric_row.f1.iloc[0]) if len(metric_row) else np.nan,
            "b2_fpr": float(metric_row.fpr.iloc[0]) if len(metric_row) else np.nan,
            "b2_fn_rate": float(metric_row.fn.iloc[0] / metric_row.adversarial.iloc[0]) if len(metric_row) and metric_row.adversarial.iloc[0] else np.nan,
        })
    return pd.DataFrame(rows)


def dataset_overlap(training: pd.DataFrame, prompts: pd.DataFrame) -> pd.DataFrame:
    train_raw = set(training.prompt_text.astype(str))
    train_normalized = {normalized_text(text) for text in training.prompt_text}
    rows = []
    for dataset, frame in prompts.groupby("dataset", sort=False):
        raw_match = frame.prompt_text.astype(str).isin(train_raw)
        normalized_match = frame.prompt_text.map(normalized_text).isin(train_normalized)
        rows.append({
            "training_dataset": "prompt_injections_train", "evaluation_dataset": dataset, "evaluation_rows": len(frame),
            "exact_duplicate_count": int(raw_match.sum()), "exact_duplicate_percentage": float(raw_match.mean() * 100),
            "normalized_exact_duplicate_count": int(normalized_match.sum()), "normalized_exact_duplicate_percentage": float(normalized_match.mean() * 100),
            "approximate_method_used": False,
        })
    return pd.DataFrame(rows)


def _classification_metrics(frame: pd.DataFrame, predictions: np.ndarray, score: np.ndarray) -> dict:
    truth = frame.true_label.to_numpy(dtype=int)
    positives, negatives = int((truth == 1).sum()), int((truth == 0).sum())
    tp = int(((truth == 1) & (predictions == 1)).sum()); tn = int(((truth == 0) & (predictions == 0)).sum())
    fp = int(((truth == 0) & (predictions == 1)).sum()); fn = int(((truth == 1) & (predictions == 0)).sum())
    mixed = positives > 0 and negatives > 0
    return {
        "rows": len(frame), "benign": negatives, "adversarial": positives,
        "auroc": roc_auc_score(truth, score) if mixed else np.nan,
        "auprc": average_precision_score(truth, score) if mixed else np.nan,
        "precision": precision_score(truth, predictions, zero_division=0) if positives else np.nan,
        "recall": recall_score(truth, predictions, zero_division=0) if positives else np.nan,
        "f1": f1_score(truth, predictions, zero_division=0) if positives else np.nan,
        "fpr": fp / negatives if negatives else np.nan, "tp": tp, "tn": tn, "fp": fp, "fn": fn,
    }


def threshold_analysis(results: pd.DataFrame) -> pd.DataFrame:
    b2 = results[results.condition == "B2"].copy()
    rows = []
    groups = list(b2.groupby("dataset", sort=False)) + [("__aggregate_micro__", b2)]
    for dataset, frame in groups:
        for threshold in THRESHOLDS:
            predictions = (frame.ml_score.to_numpy() >= threshold).astype(int)
            row = {"dataset": dataset, "threshold": threshold, "aggregation": "per_dataset" if dataset != "__aggregate_micro__" else "micro_pooled_fixed_rows"}
            row.update(_classification_metrics(frame, predictions, frame.ml_score.to_numpy()))
            rows.append(row)
    return pd.DataFrame(rows)


def linear_svm_analysis(training: pd.DataFrame, prompts: pd.DataFrame) -> tuple[pd.DataFrame, Pipeline]:
    model = Pipeline([
        ("tfidf", TfidfVectorizer(max_features=5000, analyzer="word", ngram_range=(1, 1), lowercase=True, min_df=1, max_df=1.0, norm="l2", use_idf=True, smooth_idf=True, sublinear_tf=False)),
        ("svm", LinearSVC(C=1.0, class_weight=None, dual="auto", fit_intercept=True, max_iter=1000, random_state=42, tol=1e-4)),
    ])
    model.fit(training.prompt_text, training.label)
    rows = []
    all_latencies = []
    for dataset, frame in prompts.groupby("dataset", sort=False):
        import time
        dataset_latencies, predictions, scores = [], [], []
        for prompt in frame.prompt_text:
            started = time.perf_counter()
            score = float(model.decision_function([prompt])[0])
            dataset_latencies.append((time.perf_counter() - started) * 1000)
            scores.append(score); predictions.append(int(score >= 0.0))
        row = {"dataset": dataset, "aggregation": "per_dataset"}
        row.update(_classification_metrics(frame, np.asarray(predictions), np.asarray(scores)))
        row.update({"median_latency_ms": float(np.median(dataset_latencies)), "p95_latency_ms": float(np.quantile(dataset_latencies, .95))})
        rows.append(row); all_latencies.extend(dataset_latencies)
    scores = model.decision_function(prompts.prompt_text); predictions = (scores >= 0).astype(int)
    aggregate = {"dataset": "__aggregate_micro__", "aggregation": "micro_pooled_fixed_rows"}
    aggregate.update(_classification_metrics(prompts, predictions, scores))
    aggregate.update({"median_latency_ms": float(np.median(all_latencies)), "p95_latency_ms": float(np.quantile(all_latencies, .95))})
    rows.append(aggregate)
    return pd.DataFrame(rows), model


def wildjailbreak_statistics(prompts: pd.DataFrame, results: pd.DataFrame) -> dict:
    raw = pd.read_json(PROJECT_ROOT / "datasets" / "wildjailbreak_eval.jsonl", lines=True)
    benign = raw[raw.label == "adversarial_benign"].copy()
    normalized = benign.prompt.map(normalized_text)
    b2 = results[(results.dataset == "wildjailbreak_eval") & (results.condition == "B2")]
    term_rates = {term: float(benign.prompt.str.contains(rf"\b{re.escape(term)}\b", case=False, regex=True).mean()) for term in TRIGGER_TERMS}
    safety_rate = float(benign.prompt.str.contains("|".join(SAFETY_TERMS), case=False, regex=True).mean())
    return {
        "raw_rows": len(raw), "raw_columns": list(raw.columns), "raw_label_counts": raw.label.value_counts().to_dict(),
        "raw_split_counts": raw.split.value_counts().to_dict(), "prompt_field": "prompt",
        "adversarial_benign_rows": len(benign), "adversarial_benign_internal_exact_duplicates": int(normalized.duplicated().sum()),
        "adversarial_benign_safety_term_rate": safety_rate, "adversarial_benign_trigger_term_rates": term_rates,
        "b2_false_positives": int(b2.fp.iloc[0]), "b2_true_negatives": int(b2.tn.iloc[0]), "b2_fpr": float(b2.fpr.iloc[0]),
    }


def _correlation_text(shift: pd.DataFrame) -> str:
    evaluation = shift[shift.dataset != "prompt_injections_train"]
    pieces = []
    for outcome in ("b2_f1", "b2_fpr", "b2_fn_rate"):
        valid = evaluation[["tfidf_centroid_cosine_to_training", outcome]].dropna()
        if len(valid) >= 3:
            rho, pvalue = spearmanr(valid.iloc[:, 0], valid.iloc[:, 1])
            pieces.append(f"{outcome}: Spearman rho={rho:.3f}, p={pvalue:.3f}, n={len(valid)}")
    return "; ".join(pieces)


def write_report(output: Path, fp: pd.DataFrame, fn: pd.DataFrame, rules: pd.DataFrame, categories: pd.DataFrame, features: pd.DataFrame, triggers: pd.DataFrame, shift: pd.DataFrame, overlap: pd.DataFrame, thresholds: pd.DataFrame, svm: pd.DataFrame, wild: dict, phase1: pd.DataFrame) -> None:
    error_base = phase1[phase1.condition.isin(["B2", "B3"])].copy()
    fp_summary = error_base[["dataset", "condition", "fp", "benign", "fpr"]].rename(columns={"fp": "false_positives", "fpr": "false_positive_rate"})
    fn_summary = error_base[["dataset", "condition", "fn", "adversarial"]].rename(columns={"fn": "false_negatives"})
    fn_summary["false_negative_rate"] = fn_summary.false_negatives.div(fn_summary.adversarial.replace(0, np.nan))
    fp_counts = fp_summary.to_string(index=False)
    fn_counts = fn_summary.to_string(index=False)
    top_pos = ", ".join(features[features.direction == "positive"].head(15).feature)
    top_neg = ", ".join(features[features.direction == "negative"].head(15).feature)
    aggregate_thresholds = thresholds[thresholds.dataset == "__aggregate_micro__"]
    best_f1 = aggregate_thresholds.loc[aggregate_thresholds.f1.idxmax()]
    svm_aggregate = svm[svm.dataset == "__aggregate_micro__"].iloc[0]
    b2_aggregate = phase1[(phase1.condition == "B2")]
    b2_micro = pd.read_csv(PROJECT_ROOT / "results" / "revision" / "detection" / "metrics_by_condition.csv").query("condition == 'B2'").iloc[0]
    lines = [
        "# AETHON Phase 1.5 — Error Analysis and Detector Diagnosis", "",
        "This analysis uses the fixed Phase 1 predictions and the leakage-free revision classifier. It does not alter Phase 1 artifacts, retrain AETHON, invoke an LLM, or change labels.", "",
        "## False positives", "", "```text", fp_counts, "```", "",
        "## False negatives", "", "```text", fn_counts, "```", "",
        "## WildJailbreak diagnosis", "",
        f"The loader selects the raw `prompt` field and maps `adversarial_benign` to 0 and `adversarial_harmful` to 1. Counts are {wild['raw_label_counts']}. The B2 benign result is FP={wild['b2_false_positives']}, TN={wild['b2_true_negatives']}, FPR={wild['b2_fpr']:.4f}.",
        f"All local rows have raw `split` distribution `{wild['raw_split_counts']}`. The value `train` is a local metadata anomaly for a file whose 210/2000 counts match the official evaluation construction; the loader correctly does not use this field as the class label. There are {wild['adversarial_benign_internal_exact_duplicates']} normalized exact duplicates within the 210 adversarial-benign prompts.",
        f"Safety/refusal vocabulary occurs in {wild['adversarial_benign_safety_term_rate']:.1%} of adversarial-benign prompts. The official [WildJailbreak dataset card](https://huggingface.co/datasets/allenai/wildjailbreak) defines these as benign-intent prompts deliberately transformed to resemble jailbreaks, specifically to measure exaggerated safety behavior. The [paper](https://arxiv.org/abs/2406.18510) describes the same contrastive construction.",
        "Therefore the loader mapping is faithful, but `benign` here does not mean ordinary benign traffic. The result diagnoses inability to distinguish malicious intent from adversarial form. No relabeling is justified.", "",
        "## Heuristic diagnosis", "",
        f"The eight literal regex rules collectively detect only the narrow phrases they encode. Top missed-category keyword assignments are:\n\n{categories.to_string(index=False)}", "",
        "Rules are overlapping; per-rule coverage must not be summed. The approximately 0.7% recall follows from sparse literal coverage, especially failure on role-play, indirect, semantic, and obfuscated attacks.", "",
        "## Logistic-regression features", "", f"Strongest positive features: {top_pos}.", "", f"Strongest negative features: {top_neg}.", "",
        f"Requested trigger-term coefficients and their B2 false-positive versus true-negative occurrence rates are recorded separately. Positive coefficients indicate association with the training attack class, not causal responsibility for any individual error.", "",
        "## Distribution shift", "", shift.to_string(index=False), "", f"Exploratory correlation summary: {_correlation_text(shift)}. With only five evaluation domains, these correlations are descriptive and not causal evidence.", "",
        "## Duplicate and leakage audit", "", overlap.to_string(index=False), "",
        "Exact and conservative normalized-exact overlap are reported separately. Approximate near-duplicate matching was not used, avoiding an arbitrary similarity threshold.", "",
        "## Threshold analysis", "",
        f"At the pooled level, the highest observed F1 among the prespecified thresholds occurs at {best_f1.threshold:.1f} (F1={best_f1.f1:.4f}, precision={best_f1.precision:.4f}, recall={best_f1.recall:.4f}, FPR={best_f1.fpr:.4f}). This is diagnostic only. Selecting a threshold on these evaluation labels and reporting it on the same rows would be optimistic. Threshold selection requires a separate validation partition followed by one untouched final evaluation.", "",
        "## Linear SVM", "",
        f"The leakage-free Linear SVM pooled result is AUROC={svm_aggregate.auroc:.4f}, AUPRC={svm_aggregate.auprc:.4f}, precision={svm_aggregate.precision:.4f}, recall={svm_aggregate.recall:.4f}, F1={svm_aggregate.f1:.4f}, FPR={svm_aggregate.fpr:.4f}, median latency={svm_aggregate.median_latency_ms:.4f} ms, p95={svm_aggregate.p95_latency_ms:.4f} ms. Phase 1 B2 pooled F1={b2_micro.f1:.4f} and FPR={b2_micro.fpr:.4f}.", "",
        "## Conclusions by evidence strength", "",
        "### Confirmed", "",
        "- B1 recall is low because its eight literal patterns match very few adversarial rows.",
        "- B3 differs from B2 only where the heuristic catches an ML-negative prompt; Phase 1 adds three true positives and no additional false positives.",
        "- WildJailbreak adversarial-benign samples intentionally have jailbreak form despite benign intent; the mapping is faithful to the source semantics.",
        "- B3 and B4 remain detector-equivalent; this analysis does not modify either.",
        "- Exact overlap results are shown in `dataset_overlap.csv`.", "",
        "### Supported but not causal", "",
        "- Lexical/domain shift and class prevalence vary substantially across evaluation datasets and coincide with large performance differences.",
        "- Training-feature associations explain why jailbreak-shaped benign prompts can receive high attack scores, but coefficients alone do not prove individual-error causation.", "",
        "### Not supported", "",
        "- There is no evidence that the WildJailbreak 0/1 mapping is accidentally reversed.",
        "- The current analysis does not justify relabeling WildJailbreak or choosing a new threshold on the final evaluation set.",
        "- It does not establish that distribution shift causes the observed errors.", "",
        "## Scientifically defensible next experiments", "",
        "1. Create a training-only validation split (or nested cross-validation confined to training data) for threshold selection, then freeze the threshold before final testing.",
        "2. Add representative adversarial-benign hard negatives only through a new, provenance-controlled training/validation design; retain the present leakage-free model as the locked baseline.",
        "3. Evaluate character/word n-grams and calibrated linear models as explicit ablations rather than silently changing AETHON.",
        "4. Treat ordinary benign and adversarial-benign FPR as separate constructs in the paper.",
        "5. Proceed to transformer/guardrail comparisons only as a later approved phase.", "",
    ]
    (output / "wildjailbreak_diagnosis.md").write_text("\n".join(lines[lines.index("## WildJailbreak diagnosis"):lines.index("## Heuristic diagnosis")]) + "\n", encoding="utf-8")
    (output / "PHASE_1_5_DIAGNOSIS_DATA.json").write_text(json.dumps(wild, indent=2), encoding="utf-8")
    (output / "PHASE_1_5_REPORT.md").write_text("\n".join(lines), encoding="utf-8")


def run_analysis(phase1_path=DEFAULT_PHASE1, model_path=DEFAULT_MODEL, output=DEFAULT_OUTPUT) -> dict:
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    results = pd.read_csv(phase1_path, dtype={"prompt_id": str})
    phase1_metrics = pd.read_csv(Path(phase1_path).parent / "metrics_by_dataset.csv")
    prompts = load_evaluation_prompts()
    training = load_dataset("prompt_injections_train")
    model = joblib.load(model_path)
    fp, fn, private = error_frames(results, prompts)
    _write_table(fp, output / "false_positives.csv"); _write_table(fn, output / "false_negatives.csv")
    private.to_csv(output / "private_false_positive_text.csv", index=False)
    rules, categories = heuristic_rule_coverage(prompts)
    _write_table(rules, output / "heuristic_rule_coverage.csv", markdown=True)
    _write_table(categories, output / "heuristic_missed_categories.csv", markdown=True)
    features, triggers = lr_feature_analysis(model)
    b2_private_fp = private[private.condition == "B2"]
    benign_prompts = prompts[prompts.true_label == 0].copy()
    benign_prompts["prompt_sha256"] = benign_prompts.prompt_text.map(lambda text: hashlib.sha256(text.encode("utf-8")).hexdigest())
    fp_hashes = set(b2_private_fp.prompt_sha256)
    true_negative_text = benign_prompts[~benign_prompts.prompt_sha256.isin(fp_hashes)].prompt_text
    for index, term in enumerate(triggers.term):
        expression = rf"\b{re.escape(term)}\b"
        triggers.loc[index, "b2_false_positive_count_with_term"] = int(b2_private_fp.prompt_text.str.contains(expression, case=False, regex=True).sum())
        triggers.loc[index, "b2_false_positive_presence_rate"] = float(b2_private_fp.prompt_text.str.contains(expression, case=False, regex=True).mean())
        triggers.loc[index, "b2_true_negative_count_with_term"] = int(true_negative_text.str.contains(expression, case=False, regex=True).sum())
        triggers.loc[index, "b2_true_negative_presence_rate"] = float(true_negative_text.str.contains(expression, case=False, regex=True).mean())
    _write_table(features, output / "lr_top_features.csv"); _write_table(triggers, output / "lr_trigger_terms.csv")
    shift = distribution_shift(model, training, prompts, phase1_metrics)
    _write_table(shift, output / "distribution_shift.csv")
    overlap = dataset_overlap(training, prompts); _write_table(overlap, output / "dataset_overlap.csv")
    thresholds = threshold_analysis(results); _write_table(thresholds, output / "threshold_analysis.csv")
    svm, _ = linear_svm_analysis(training, prompts); _write_table(svm, output / "linear_svm_results.csv")
    (output / "linear_svm_comparison.tex").write_text(svm.to_latex(index=False, na_rep="NA", float_format="%.6f"), encoding="utf-8")
    wild = wildjailbreak_statistics(prompts, phase1_metrics)
    write_report(output, fp, fn, rules, categories, features, triggers, shift, overlap, thresholds, svm, wild, phase1_metrics)
    return {"false_positives": len(fp), "false_negatives": len(fn), "output": str(output)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run local Phase 1.5 detector error analysis.")
    parser.add_argument("--phase1-results", default=str(DEFAULT_PHASE1))
    parser.add_argument("--model-path", default=str(DEFAULT_MODEL))
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()
    print(json.dumps(run_analysis(args.phase1_results, args.model_path, args.output_root), indent=2))


if __name__ == "__main__":
    main()

# Research protocol 2026

Status: PARTIAL. Dataset audit, nested training selection, paired statistics,
offline ProtectAI smoke and synthetic DP utility have local implementations.
See RESEARCH_2026_REPORT.md for actual executions and outstanding experiments.
Initial host process creation failures were intermittent and subsequently cleared.

The five-source 9,139-row historical pool is a previously inspected reference
benchmark. Neither its labels nor its errors may select new models or thresholds.
Historical metrics remain historical evidence. Do not overwrite their artifacts.
Only prompt_injections_train is authorized for current model selection. Examples
elsewhere recommending training on prompt_injection_core are superseded here.

Before training, audit stable source row IDs, normalized-text SHA-256 (Unicode
NFKC, whitespace collapse), exact and approximate duplicates, conflicting labels,
label provenance and cross-partition overlaps. Keep raw-text hashes separately.
Deduplicate/group related training rows before splitting. Do not remove historical
test rows; report overlap flags and sensitivity analyses. A prospective independent
test must be collected after freezing model, threshold and judgment rubric, with
semantic overlap review by reviewers blinded to detector outcomes.

Estimate selection performance using outer stratified folds: fit representations,
calibration and threshold selection exclusively inside each outer training fold.
Choose thresholds for the complete heuristic OR statistical decision, since the
heuristic imposes a minimum FPR. Report infeasible caps explicitly. Inner OOF
selection scores are not unbiased estimates of selected-model performance.
Final refitting must not access reference benchmark labels. Preserve original B3.

Compare word/character logistic regression, character LinearSVC and sigmoid
calibrated LinearSVC. Margins are not probabilities. Calibrate the full text
pipeline inside folds; do not fit the vectorizer on calibration validation data.
Isotonic needs a prespecified adequate calibration sample size; otherwise disable.
Report ROC/PR, Brier, ECE with bin definition, reliability diagrams, FPR by
dataset/benign subgroup, adversarial recall, precision, F1 and recall at FPR caps.

Paired comparisons require unique (dataset, source row ID, text hash) keys and
identical truth labels. Reject missing or duplicate keys. McNemar compares paired
correctness on both true classes. Bootstrap differences with the same sampled
indices for both methods; report clustering assumptions, seed, 95% intervals,
hypothesis, sample size and multiplicity policy. Source/family cluster sensitivity
analysis is required when dependencies are plausible.

Every future run must record run ID, commit and dirty state, dataset/model hashes,
pinned model and tokenizer revisions, representation, threshold, seed, temperature,
token limits, environment/dependencies/hardware, duration/status, expected and
processed counts, checkpoint fingerprint, errors and justified exclusions.
Write checkpoints atomically and reject incompatible resumes. Export aggregate
CSV, JSON, Markdown and LaTeX without raw attack text or full responses.

DP concerns released counters, not raw prompt confidentiality. Define adjacency
and contribution bounds before claiming sensitivity one. For epsilon 0.5, 1.2,
2.5, measure repeated noise draws, absolute/relative error (undefined at zero),
variance and sequential composition. B3/B4 decisions must match exactly.
Separate preprocessing, heuristic, classifier, decision, audit, LLM and end-to-end
latencies; document warmup, batch size and hardware and report p50/p95/p99.
Do not pool local CPU and cloud GPU timings.

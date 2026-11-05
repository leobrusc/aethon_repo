# Detector generalization

See EXPERIMENT_PROTOCOL_2026.md for data/selection policy. The legacy
`model_selection.cross_validate` reuses OOF predictions for candidate/threshold
selection and reporting. Its outputs are selection diagnostics, not unbiased
post-selection estimates. Its vectorizer is also fitted outside calibration folds.
Do not use that entry point for new confirmatory studies. Historical outputs remain.

`research_generalization.py` implements nested StratifiedGroupKFold, grouping
normalized exact duplicates. Sigmoid calibration wraps the complete TF-IDF pipeline.
Selection uses only prompt_injections_train. Isotonic is disabled for 546 examples.
No online learning is introduced. Defaults compare five word/character/union
LR/SVC configurations, with five outer and three inner folds; sigmoid calibration
uses three grouped folds inside each fit.

Threshold candidates are OOF scores plus an above-maximum threshold. Maximize F1
under FPR <= 0.10 for the complete heuristic OR classifier decision. An infeasible
heuristic floor fails explicitly. A validation cap is not a future FPR guarantee.
Raw SVC margins define `research_margin_or_v2026`; probability models define
`research_probability_or_v2026`. Neither silently replaces historical B3/B4.

Run `python src/research_generalization.py --run-id <new-id>`; `--smoke` uses two
candidates/two outer folds. Exports: outer predictions, inner choices, selection
OOF, frozen configuration, fitted versioned model/hash, ROC/PR CSV/SVG and
probability-only Brier/ECE/reliability bins. ECE uses ten equal-width bins on the
statistical branch. Do not pool ranking metrics across heterogeneous score scales.
Completed reruns validate hashes; changed code/data/dependencies reject resume.
Interrupted fitting restarts deterministically without partial estimator reuse.

McNemar now validates unique source-row pairing. `research_paired.py` supplies
paired/clustered percentile intervals. Statistical tests remain exploratory unless
hypotheses and multiplicity are prespecified. Five dataset clusters give weak
cluster-bootstrap precision.

Historical B3 remains the reference; no robust superiority claim is established.
notinject/wildjailbreak_eval may supply descriptive subgroup reports, never new
thresholds. Exact/near screening is implemented. Semantic review and prospective
independent data remain pending. Training-only nested performance cannot establish
out-of-distribution generalization.

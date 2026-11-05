# AETHON Phase 1.5 — Error Analysis and Detector Diagnosis

This analysis uses the fixed Phase 1 predictions and the leakage-free revision classifier. It does not alter Phase 1 artifacts, retrain AETHON, invoke an LLM, or change labels.

## False positives

```text
                 dataset condition  false_positives  benign  false_positive_rate
  prompt_injections_test        B2                0      56             0.000000
  prompt_injections_test        B3                0      56             0.000000
   prompt_injection_core        B2              267    2538             0.105201
   prompt_injection_core        B3              267    2538             0.105201
jailbreakbench_behaviors        B2               26     100             0.260000
jailbreakbench_behaviors        B3               26     100             0.260000
      wildjailbreak_eval        B2              201     210             0.957143
      wildjailbreak_eval        B3              201     210             0.957143
               notinject        B2              118     339             0.348083
               notinject        B3              118     339             0.348083
```

## False negatives

```text
                 dataset condition  false_negatives  adversarial  false_negative_rate
  prompt_injections_test        B2               24           60             0.400000
  prompt_injections_test        B3               24           60             0.400000
   prompt_injection_core        B2             2416         3736             0.646681
   prompt_injection_core        B3             2413         3736             0.645878
jailbreakbench_behaviors        B2               75          100             0.750000
jailbreakbench_behaviors        B3               75          100             0.750000
      wildjailbreak_eval        B2              166         2000             0.083000
      wildjailbreak_eval        B3              166         2000             0.083000
               notinject        B2                0            0                  NaN
               notinject        B3                0            0                  NaN
```

## WildJailbreak diagnosis

The loader selects the raw `prompt` field and maps `adversarial_benign` to 0 and `adversarial_harmful` to 1. Counts are {'adversarial_harmful': 2000, 'adversarial_benign': 210}. The B2 benign result is FP=201, TN=9, FPR=0.9571.
All local rows have raw `split` distribution `{'train': 2210}`. The value `train` is a local metadata anomaly for a file whose 210/2000 counts match the official evaluation construction; the loader correctly does not use this field as the class label. There are 0 normalized exact duplicates within the 210 adversarial-benign prompts.
Safety/refusal vocabulary occurs in 46.2% of adversarial-benign prompts. The official [WildJailbreak dataset card](https://huggingface.co/datasets/allenai/wildjailbreak) defines these as benign-intent prompts deliberately transformed to resemble jailbreaks, specifically to measure exaggerated safety behavior. The [paper](https://arxiv.org/abs/2406.18510) describes the same contrastive construction.
Therefore the loader mapping is faithful, but `benign` here does not mean ordinary benign traffic. The result diagnoses inability to distinguish malicious intent from adversarial form. No relabeling is justified.

## Heuristic diagnosis

The eight literal regex rules collectively detect only the narrow phrases they encode. Top missed-category keyword assignments are:

              category  missed_attacks  share_of_all_missed
  instruction_override            1096             0.187254
     role_manipulation            1250             0.213566
     jailbreak_framing             188             0.032120
  encoding_obfuscation              55             0.009397
semantic_reformulation             377             0.064411
    indirect_injection              43             0.007347
                 other            2844             0.485905

Rules are overlapping; per-rule coverage must not be summed. The approximately 0.7% recall follows from sparse literal coverage, especially failure on role-play, indirect, semantic, and obfuscated attacks.

## Logistic-regression features

Strongest positive features: you, sie, the, write, that, forget, all, everything, your, du, alle, vergiss, ignore, instructions, schreibe.

Strongest negative features: deutschland, welche, ukraine, europa, corona, hat, europe, what, which, did, germany, like, in, my, can.

Requested trigger-term coefficients and their B2 false-positive versus true-negative occurrence rates are recorded separately. Positive coefficients indicate association with the training attack class, not causal responsibility for any individual error.

## Distribution shift

                 dataset  rows  adversarial_prevalence  tfidf_centroid_cosine_to_training  vocabulary_coverage  oov_rate  mean_words  median_words  p95_words    b2_f1   b2_fpr  b2_fn_rate
 prompt_injections_train   546                0.371795                           1.000000             1.000000  0.000000   19.443223          10.0      52.00      NaN      NaN         NaN
  prompt_injections_test   116                0.517241                           0.796446             0.769705  0.230295   20.120690          12.0      59.00 0.750000 0.000000    0.400000
   prompt_injection_core  6274                0.595473                           0.468238             0.664569  0.335431   20.030124           8.0      68.35 0.495961 0.105201    0.646681
jailbreakbench_behaviors   200                0.500000                           0.426258             0.586079  0.413921   12.915000          13.0      20.00 0.331126 0.260000    0.750000
      wildjailbreak_eval  2210                0.904977                           0.577278             0.633236  0.366764  120.598190         107.0     247.10 0.909046 0.957143    0.083000
               notinject   339                0.000000                           0.529128             0.626487  0.373513   13.283186          15.0      27.00      NaN 0.348083         NaN

Exploratory correlation summary: b2_f1: Spearman rho=0.800, p=0.200, n=4; b2_fpr: Spearman rho=-0.100, p=0.873, n=5; b2_fn_rate: Spearman rho=-0.800, p=0.200, n=4. With only five evaluation domains, these correlations are descriptive and not causal evidence.

## Duplicate and leakage audit

       training_dataset       evaluation_dataset  evaluation_rows  exact_duplicate_count  exact_duplicate_percentage  normalized_exact_duplicate_count  normalized_exact_duplicate_percentage  approximate_method_used
prompt_injections_train   prompt_injections_test              116                      0                         0.0                                 0                                    0.0                    False
prompt_injections_train    prompt_injection_core             6274                      0                         0.0                                 0                                    0.0                    False
prompt_injections_train jailbreakbench_behaviors              200                      0                         0.0                                 0                                    0.0                    False
prompt_injections_train       wildjailbreak_eval             2210                      0                         0.0                                 0                                    0.0                    False
prompt_injections_train                notinject              339                      0                         0.0                                 0                                    0.0                    False

Exact and conservative normalized-exact overlap are reported separately. Approximate near-duplicate matching was not used, avoiding an arbitrary similarity threshold.

## Threshold analysis

At the pooled level, the highest observed F1 among the prespecified thresholds occurs at 0.2 (F1=0.7863, precision=0.6501, recall=0.9947, FPR=0.9735). This is diagnostic only. Selecting a threshold on these evaluation labels and reporting it on the same rows would be optimistic. Threshold selection requires a separate validation partition followed by one untouched final evaluation.

## Linear SVM

The leakage-free Linear SVM pooled result is AUROC=0.6890, AUPRC=0.8087, precision=0.7596, recall=0.6528, F1=0.7022, FPR=0.3756, median latency=0.2334 ms, p95=0.3621 ms. Phase 1 B2 pooled F1=0.6613 and FPR=0.1887.

## Conclusions by evidence strength

### Confirmed

- B1 recall is low because its eight literal patterns match very few adversarial rows.
- B3 differs from B2 only where the heuristic catches an ML-negative prompt; Phase 1 adds three true positives and no additional false positives.
- WildJailbreak adversarial-benign samples intentionally have jailbreak form despite benign intent; the mapping is faithful to the source semantics.
- B3 and B4 remain detector-equivalent; this analysis does not modify either.
- Exact overlap results are shown in `dataset_overlap.csv`.

### Supported but not causal

- Lexical/domain shift and class prevalence vary substantially across evaluation datasets and coincide with large performance differences.
- Training-feature associations explain why jailbreak-shaped benign prompts can receive high attack scores, but coefficients alone do not prove individual-error causation.

### Not supported

- There is no evidence that the WildJailbreak 0/1 mapping is accidentally reversed.
- The current analysis does not justify relabeling WildJailbreak or choosing a new threshold on the final evaluation set.
- It does not establish that distribution shift causes the observed errors.

## Scientifically defensible next experiments

1. Create a training-only validation split (or nested cross-validation confined to training data) for threshold selection, then freeze the threshold before final testing.
2. Add representative adversarial-benign hard negatives only through a new, provenance-controlled training/validation design; retain the present leakage-free model as the locked baseline.
3. Evaluate character/word n-grams and calibrated linear models as explicit ablations rather than silently changing AETHON.
4. Treat ordinary benign and adversarial-benign FPR as separate constructs in the paper.
5. Proceed to transformer/guardrail comparisons only as a later approved phase.

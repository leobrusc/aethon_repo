# Data independence audit v1.0.0

**PILOT_BLOCKED.** Inspection of baseline `9ed55709`, not a new semantic audit.

| Pool | Observed evidence and allowed use | Unresolved |
| --- | --- | --- |
| Training | 546 rows; only authorized model-selection source | Semantic/family provenance |
| Reference | 9,139 repeatedly inspected rows; regression/context only | Cannot regain unseen status by re-splitting |
| Existing integrity audit | 9,685 total rows, 201 exact groups, 636 lexical-near pairs | Semantic audit NOT_RUN |
| Train/reference overlap | Zero normalized exact groups; one lexical-near pair at cosine >=0.95 | Blinded pair and semantic adjudication |
| Nested study | Grouped folds; representation/calibration fitted inside training folds | Not an independent external final test |
| Historical smoke | 21 bounded/adaptively inspected interface cases | Not an IID efficacy/power sample |
| New public unit fixtures | Four synthetic development rows | Never pilot/final evaluation data |
| Proposed pilot | 12 attacks + 12 matched clean controls | Private pool/license/review/seal absent |
| Final holdout | Must be acquired after preregistration and hidden from selection | Sampling frame, power and seal absent |

Counts come from `docs/research_2026_evidence/integrity/summary.json` and its
manifest/index. Normalization was NFKC + whitespace collapse, case preserved.
The near screen was corpus-fitted char_wb TF-IDF 3–5; it was lexical discovery,
not proof of semantic novelty or a detector performance estimate.

## Leakage/dependence register

- Exact copies, repackaged benchmarks, raw/normalized variants and duplicated IDs:
  compare against ALL training, reference, nested-development and smoke materials,
  including restricted private smoke inputs. Missing access is NOT_AUDITED, not zero.
- Paraphrases, translations, shared generation seeds, task templates and attack
  families: pin semantic model/revision/hash and calibrate its candidate threshold
  on separate development pairs BEFORE final inspection. Neither is frozen here.
  Two blinded reviewers adjudicate candidates; an embedding score alone is not a seal.
- Model-pretraining contamination of public datasets remains NOT_AUDITED even
  when local overlap tests pass. Collection time does not prove training novelty.
- Reference/pilot-guided prompt, rubric or threshold tuning; final-label exposure;
  reviewer awareness of condition; best-seed/retry selection: separate steward,
  developer and reviewer roles, keep a decision log and final labels hidden.
- Conditions, variants, translations and B4 reused responses are dependent. Keep
  their task/template/source-family cluster together; 120 slots are not 120
  independent trials. Use source/family grouping sensitivity in final analysis.

## Required seal

Before model access, a steward records licensed source/row/task/family IDs,
collection timestamps, label provenance, objectives/oracles, raw and normalized
hashes. Exact/lexical screening and pinned semantic review must cover the entire
known prior inventory. Keep historical rows unchanged; assign overlap flags and
pre-output exclusion reasons in the NEW inventory. Preserve both reviewer votes
and adjudication, hash/sign the ledger, inventory and protocol. Pilot quotas are
purposive (no population inclusion probabilities); final sampling requires a frame,
strata and known inclusion probabilities. Every pilot case is excluded from final
confirmatory data. Final acquisition starts only after signed preregistration.

The raw red-team LFS OID proves continuity only; independent canonical digest
remains **NOT_AUDITED**. No dataset is normalized or edited to satisfy this audit.
Offline preflight checks receipt identities, not semantic review or authorization.

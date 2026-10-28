# BENCHMARK STATUS — AETHON

## 2026-10-28 research consolidation

See [the 2026 execution report](docs/RESEARCH_2026_REPORT.md) and
[protocol](docs/EXPERIMENT_PROTOCOL_2026.md). Local validation: **106 passed**.
The historical 9,139-row reference pool is preserved and previously inspected.
New evidence covers dataset overlap audit, training-only nested selection,
18-prompt cached-weight ProtectAI smoke, paired tooling smoke and synthetic DP.
No target LLM evaluation, cloud provisioning or full modern baseline run occurred.
The status below is retained as historical context.

**Updated:** 2026-09-10  
**Scope:** local revision experiments for the BRACIS reviewer response.

## Current validated state

- Branch: `revision/bracis-reviewer-experiments`
- Local reliability head: `55407e7e998bb58a4cc3f8426e63dcd6ee77e761`
- Automated tests: **57 passed, 1 warning**
- Full GPU evaluation: **not executed**; GPU infrastructure was intentionally skipped.
- Meta Prompt Guard 2: not evaluated because gated Hugging Face access was unavailable.
- ProtectAI DeBERTa v2: adapter and local smoke/recovery flow validated, but no complete 9,139-prompt publication benchmark is claimed.

## Publication-ready local evidence

### Phase 1 — detector-only benchmark

The fixed evaluation contains 9,139 prompts across Prompt Injections Test, Prompt Injection Core, JailbreakBench Behaviors, WildJailbreak Eval, and NotInject. Prompt-level metrics are independent of target LLM identity.

| Condition | AUROC | AUPRC | Precision | Recall | F1 | FPR | Median ms | P95 ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| B1 Heuristic | 0.5033 | 0.6474 | 0.9556 | 0.0073 | 0.0145 | 0.0006 | 0.0036 | 0.0106 |
| B2 TF-IDF+LR | 0.6761 | 0.8066 | 0.8401 | 0.5453 | 0.6613 | 0.1887 | 0.6292 | 1.2264 |
| B3 AETHON | 0.6766 | 0.8075 | 0.8402 | 0.5458 | 0.6617 | 0.1887 | 0.7152 | 1.4118 |
| B4 AETHON+DP | 0.6766 | 0.8075 | 0.8402 | 0.5458 | 0.6617 | 0.1887 | 0.7091 | 1.3641 |

B3 and B4 are detection-equivalent by design and were empirically identical.

### Phase 1.5 — error analysis

- Heuristic coverage: 43 of 5,896 adversarial prompts (~0.7% recall).
- WildJailbreak adversarial-benign FPR: 0.9571 for B3.
- No exact or normalized-exact overlap was found between the 546-row training set and any final evaluation dataset.
- Results indicate substantial cross-domain shift and over-defense, but do not establish a causal mechanism.

### Phase 2 — leakage-free lightweight model selection

Training-only 5-fold CV selected character TF-IDF (`char_wb`, 3–5) + calibrated LinearSVC with threshold 0.48. OOF metrics were AUROC=0.9697, F1=0.9124, FPR=0.0233. After freezing the configuration and evaluating once on the 9,139 external rows, V2 achieved AUROC=0.6734, F1=0.6892, and FPR=0.4561.

The V2 variant therefore improves recall/F1 but substantially worsens false-positive rate and does **not** replace the B3 Logistic Regression baseline.

## Scientific interpretation

The revised evidence supports a narrower and more defensible AETHON claim:

1. L1 is a very-low-coverage, precision-oriented fail-fast rule layer.
2. L2 provides most of the current discriminative capability.
3. The earlier target-model-specific AUROC organization is obsolete for prompt-level detection.
4. Cross-domain calibration and over-defense are the main observed weaknesses.
5. Modern transformer comparison remains incomplete and must be reported as a limitation, not inferred from smoke tests.

## Report

The standalone Overleaf report is maintained under:

`docs/overleaf_experiment_report/main.tex`

Repository branch:

https://github.com/leobrusc/aethon_repo/tree/revision/bracis-reviewer-experiments

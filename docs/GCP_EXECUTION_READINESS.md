# GCP execution readiness

Baseline pipeline is ready for a controlled GPU smoke after environment setup.
Full baseline evaluation: NOT_RUN. Prospective LLM evaluation: PARTIAL, pending
unseen data, target snapshots, objective rubrics, secure storage and human review.
No cloud resources were provisioned and no weights were downloaded in this task.

`configs/research_2026/baselines.json` pins model and tokenizer revisions.
ProtectAI SAFE=0/INJECTION=1 was checked against its official
[configuration](https://huggingface.co/protectai/deberta-v3-base-prompt-injection-v2/raw/main/config.json).
The official [Prompt Guard metadata](https://huggingface.co/api/models/meta-llama/Llama-Prompt-Guard-2-22M)
reports gated access; its pinned local weights were absent (NOT_RUN).
Prompt Guard class semantics still need verification after access is available.

Use `research_baseline.py`, which defaults to local files only, pins revisions,
hashes weights/config/tokenizer files, validates labels, measures original token
lengths and rejects incompatible/foreign resumes. ProtectAI completed an actual
18-prompt CPU smoke using cached weights. Single/batch consistency also has a
weight-free unit test; full GPU consistency remains pending. Completed checkpoints
can finalize without loading a detector. Injection scope is not general jailbreak
detection equivalence.

Linux preparation (install the appropriate CUDA PyTorch build separately; preserve
a full dependency lock and driver/CUDA inventory for the new environment):

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pytest -q
python src/research_integrity.py --run-id integrity-gcp
python src/research_baseline.py --model protectai --revision 90c9989b1a342275dd0d1a95aad283c04e075671 --run-id protectai-gpu-smoke --device cuda --batch-size 4 --smoke
python src/research_baseline.py --model protectai --revision 90c9989b1a342275dd0d1a95aad283c04e075671 --run-id protectai-gpu-smoke --device cuda --batch-size 4 --smoke --resume
```

Absent local weights yield NOT_RUN. After separately approving weight acquisition,
add `--allow-download` to the first smoke command. After reviewing the smoke, a
full detector-only reference run uses a **new** run ID and omits `--smoke`.
No such full run is launched in this task. Record GPU model, batch size, warmup,
dependencies and timing percentiles. Do not pool CPU and GPU latencies.

```bash
python src/research_generalization.py --run-id nested-gcp
python src/research_dp.py --run-id dp-gcp
python src/research_paired.py first.csv second.csv --output results/research_2026/paired-gcp --cluster-dataset
```

Paired input: dataset, prompt_id, prompt_sha256, true_label, prediction. Filter one
frozen detector/condition per CSV. Mismatched rows, duplicate keys and conflicting
truth fail explicitly. Only five dataset clusters limit bootstrap precision.
`prospective_targets.json` records target settings; null revisions intentionally
prevent claiming readiness for a confirmatory LLM run.

# Prospective preparation validation

Engineering baseline: `9ed55709add0fc45f63847a0394315863faa0876`.

- PASS: 17 new software-only tests and 161 full tests, one expected mock-download warning.
- PASS: Ruff, 127 protected files, 31 indexed evidence payloads and six historical manifests.
- PASS: offline preflight returned expected exit 2 / PILOT_BLOCKED, four synthetic fixture IDs, campaign_executed=false. No frozen-file mismatch.
- PASS: documentary branch's 144 baseline tests, Ruff and scientific hash verifiers.
- PASS: 122 prior post-merge evidence copies and byte-identical report, plus original five user-file hashes.
- PASS: no historical result/dataset, dependency declaration, lock or baseline source file changed.

Commands/cwd/exit codes/raw-output SHA-256 values are in `validation-v1/checks.json`;
the adjacent logs and preflight JSON preserve actual results. Newly prepared code
and fixtures were tested with the maintained Python 3.12.13 development environment,
source paths from this branch, and offline HF/dataset flags. No target model was
loaded and neither the pilot nor the final scientific campaign was executed.
Staged-diff publication guards and committed-evidence hashes are checked at publication.

The report publication branch and scientific branch are independent siblings of
the immutable baseline; neither is merged here. Their PR bodies cross-link the
documentary closure and scientific preparation without claiming scientific approval.

Classification remains **PILOT_BLOCKED**. See SCIENTIFIC_READINESS.md for named
data, semantic-review, rubric, reviewer, storage, hardware and execution gates.

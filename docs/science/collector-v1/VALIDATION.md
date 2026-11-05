# Phase 2 validation

Final local result: **203 tests PASS**, one expected mocked-download warning,
no skipped tests. This includes the 161 parent tests and 42 new synthetic
collector/governance cases. Ruff, pip check and both offline preflights PASS;
preflight exit 2 / PILOT_BLOCKED is the expected acceptance result, not a launched
pilot. Unauthorized collect invocation was rejected before any model load.

Scientific preservation PASS: 127 protected files, 31 indexed evidence artifacts,
six historical manifests, 9,139 B3/B4 pairs with zero decision mismatches, 80
published metric values recomputed from stored predictions, five hydrated LFS
payload hashes/fsck and the original five local file hashes. No new detector/LLM
inference was performed for this historical reanalysis. Dependencies, locks,
historical datasets/results and the engineering baseline were not modified.

The Python audit hook observed zero connection/DNS events. Approved local Git,
Python, read-only native security observation and OpenSSL processes are recorded
by basename only. Native/child process network isolation is NOT certified by that
hook and remains a platform gate. Production Ed25519 verification was exercised
with an ephemeral synthetic key and tampered-message negative test. No real
reviewer, receipt, trust root, approval or private production directory was created.

Development attempts are retained: the first pytest command failed before tests
because its basetemp parent did not exist; the next functional run passed 32 tests
with one platform symlink skip. A later run exposed a faulty symlink mock and a
correct seal-mismatch rejection while implementation files were changing. The
first full-session audit incorrectly assumed Windows always supplies a non-null
subprocess executable; it was corrected without allowing network access. The
199-test snapshot then passed; additional distinct-key, signed-disposition and
request/config-mutation regressions were added before the final run above.
These earlier development logs are not represented as scientific or final approval.

Exact commands, cwd, exit/expected codes and SHA-256 values are in validation/
checks.json; raw final logs and the public summary are adjacent. Generated keys,
raw synthetic run directories and private response objects are excluded from
publication. Staged publication guard and whitespace checks are required before
commit; committed output hashes and source seals are verified before push.

Actual classification remains **PILOT_BLOCKED** because all eight external gates
are PENDING. See GATE_STATUS.md and GOVERNANCE.md for closure criteria. Complete
instrumentation and green software tests do not authorize any target inference.

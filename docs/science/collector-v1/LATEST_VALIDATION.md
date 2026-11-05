# Latest phase 2 validation

**205 tests PASS**, one expected mock-download warning, zero skips. The
161 inherited tests and 44 new collector/governance cases all passed.
This supersedes the 203-test code snapshot in VALIDATION.md without overwriting
its raw evidence. The final addition records UTC event timestamps and monotonic
generation/evaluation durations in durable private checkpoints; recovery preserves
original durations. Timings do not affect request equivalence or schedule IDs and
are not presented as synthetic scientific/performance evidence.
Objects and pointers also bind the complete run fingerprint; a regression test
rejects otherwise valid hashed checkpoints copied from another run.

Ruff, pip check, 127 protected-file hashes, 31 indexed artifacts, six historical
manifests, 9,139 historical B3/B4 pairs (zero mismatches), 80 published metric values,
five LFS payload hashes/fsck and the five original local-file hashes: PASS.
Both preflights returned expected PILOT_BLOCKED/exit 2. Unauthorized collect was
rejected. Python network audit observed zero connection/DNS events. Native/child
OS network isolation and native power-loss assurances remain external review gates.

Latest commands/exit codes/output hashes: validation-v2/checks.json. Logs and gate
summary are adjacent. No target weights were loaded or downloaded, no real inference
or pilot was executed, no production ACL/root was provisioned and all eight gates
remain PENDING. **Final operational classification: PILOT_BLOCKED.**

# Abstract Lease Authority and Fencing

## State and serialization

The model now carries lease ID, holder, epoch, authority identity/state, authority serial, transfer ID/serial, revocation epoch, expected head and each outstanding publication token. A token snapshots `(writer, lease_id, epoch, expected_sequence, expected_head, authority_id, revocation_epoch)`.

Lease transfer and publish are transitions of one abstract serializing authority. `publish` atomically compares the token snapshot with the current authority, lease, holder, epoch, revocation epoch and expected head, then advances the logical head. A successful publication records its authority generation. A transfer changes lease identity and epoch and appends a distinct generation; stale outstanding tokens remain visible and are rejected.

## Required race

1. A prepares publication under lease A/epoch 7 and expected head `0/h0`.
2. The authority transfers the lease to B/epoch 8.
3. A publishes its old token: REJECT, head unchanged.
4. B prepares a token against the same expected head and publishes: accepted only if all durable response/journal and authority checks pass.

`tests/test_src02_safety_model.py` exercises this sequence and a competing-token case. The result demonstrates an abstract atomic relation only. It does not prove Linux syscall atomicity, Windows handle semantics, OS lock takeover, cross-process fencing, or that every real mutation passes through this authority. Those platform properties remain NOT_VALIDATED.

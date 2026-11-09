# Authenticated Witness Reconciliation

## Query protocol represented by the model

The model distinguishes `NONE`, `REQUESTED`, `UNAVAILABLE`, `RECEIVED`, `AUTHENTICATED`, `VALIDATED`, and `RECONCILED`. Request creation binds run, Operation ID, policy epoch and revocation epoch. An unavailable query remains blocked. A response is not trusted merely because it exists: the abstract verification transition checks signer identity, the modeled signature-valid result, freshness, revocation status and every request binding. Its `(sequence, head)` must equal the current local head, the exact predecessor, or the exact pending next tuple. The next tuple additionally requires the same committed Operation ID.

Only `witness_reconcile` after successful validation can clear the recovery block. A valid predecessor result confirms that the same Operation ID was not advanced and permits retry of that same compare-and-advance. A valid next result confirms the already committed Operation ID and can satisfy the witness requirement. Stale, replayed, misbound, ahead, behind, same-sequence-conflicting, stale-policy and stale-revocation results reject. Timeout before or after remote commit is resolved by querying the same operation; no new witness operation ID is created.

## Security boundary

The model treats signature verification and freshness as trusted abstract outcomes. It does not implement cryptography, PKI, revocation lookup, a witness service, consistency proofs, or transport authentication. Thus it verifies the control-flow condition “only after a valid verifier result,” not the verifier or deployed witness. All such native and service behavior remains NOT_VALIDATED. Unavailability and ambiguity fail closed.

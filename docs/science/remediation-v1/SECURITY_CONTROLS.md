# Security controls and support boundary

**REMEDIATION_PARTIAL; PILOT_BLOCKED.** Windows and Linux production object-bound
execution and private storage are disabled in this version.

## Executable and loader identity

The old window lay between `OpenSSLVerifier.__init__` hashing a pathname and
`subprocess.run` later opening it. `path_identity` now observes device/inode,
mode/owner/group, Windows attributes, reparse rejection and every ancestor, plus
single-link file payload SHA-256. Independently pinned dependency paths/hashes
can be supplied; altered executable, dependency or ancestor is rejected. No PATH
search or fallback exists. However, an inventory is not proof of the complete
transitive loader closure, nor does a stat/hash bind a subsequent execution.
Consequently, `__call__` never spawns OpenSSL and denies production verification.

Considered mechanisms: Linux fexecve/execveat can bind a main executable but not
automatically its ELF interpreter, DSOs, loader environment or writable parents;
Windows protected handles denying write/delete require correct loader image/ DLL
identity and complete path/ACL constraints. Neither has a validated implementation
here. Re-reading a hash, an unverified deployment receipt or a caller boolean is
not accepted as a substitute. These mechanisms need an audited native backend and
independently evidenced immutable deployment. No real malicious binary is run.

## Storage identity and writes

Observation binds the complete subject/run hash, exact absolute destination,
root/ancestor object identity and mode metadata. Its canonical fingerprint is
checked, then its identity compared with the current object before any mkdir.
The store rechecks root/ancestor identities and observed modes on access, alongside
existing run/events/object identities, capability expiry and retention. Stale,
foreign, renamed or reparse-linked roots fail. Existing atomic no-clobber object
writes, hashes, owned writer locks, durable intent and recovery remain intact.

Stat modes are not a Windows DACL/SDDL observation. No ACL-revocation protection or
absence of a later race is inferred from those comparisons. `probe_storage` keeps
read-only ACL/encryption observations but reports PENDING because no production
object-confined I/O backend is approved. `PrivateRunStore` requires such a trusted
backend and otherwise fails before writing. CLI exposes no backend override.
Synthetic tests inject a named fake, which checks identities but is explicitly not
OS confinement. There is no `approved: true`/policy flag that enables writes.

Linux deployment must address dirfd-relative no-follow traversal, writes, links,
renames, metadata/fsync and access revocation throughout the run, not just open
the root once. Windows must address stable volume/file IDs, held directory handles,
share modes, reparse traversal, inherited ACL changes and atomic/durable operations.
Exclusive trusted ancestors, encrypted volume, private backups and privileged
administrator trust require independently reviewed deployment evidence. No such
native proof is fabricated by these fixtures.

## Authentication, review and runtime isolation

The independent policy digest, receipt role/quorum/subject/time/evidence binding,
separate operator launch and in-process issued capability remain required. Assigned
evaluators now require three distinct actual key identities, including adjudicator;
aliases do not count as independent people/keys. Review envelopes are separately
signed and bind the authorized assignment, complete run, exact slot/sample/case,
response content-addressed object and approved rubric version/hash. Private spans
must match the exact generated continuation and their referenced bytes/hash.

`judge=None` remains the CLI default. Unauthenticated callbacks cannot record votes
or complete scientific review. No new egress claim is made: Python socket/Popen
interception is defense in depth only; native extensions, os.system and child
network behavior require OS containment. Trusted test injections are code-level
dependencies, not an authorization interface for untrusted inventory or receipts.

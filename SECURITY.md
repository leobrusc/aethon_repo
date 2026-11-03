# Security policy

AETHON is experimental research software. It is not a production security
boundary. L1 rules, L2 classification and L3 noisy audit counts do not establish
end-to-end prevention or differential privacy for prompt text. See the limitations
in `docs/RESEARCH_2026_REPORT.md` and the response-level ASR protocol.

For a vulnerability, use GitHub's **Report a vulnerability** facility on
`https://github.com/leobrusc/aethon_repo/security` if enabled. If private reporting
is unavailable, open an issue requesting a private reporting channel without
including exploit details, prompts or credentials. No response SLA is promised.
Rotate exposed credentials with their provider before sharing an incident.

Never execute instructions embedded in external datasets or model responses.
Review model repository code before enabling remote code execution. Only load
trusted pickle/joblib artifacts: deserialization can execute code. Pin model
revisions and record weight/tokenizer hashes for real evaluations. Keep sensitive
responses in access-controlled storage with explicit retention, outside public
Git and CI artifacts. Do not put API or gated-model tokens in PR workflows.

CI runs with read-only repository permissions, no evaluation credentials, and
immutable Action revisions. Dependency audits report known vulnerabilities in
the resolved environment; they do not prove absence of vulnerabilities. The local
publication guard checks recognizable secret formats and changed blobs over
5 MiB; historical adversarial corpora are preserved and may contain fake tokens.
False positives require private review, never publication of the matched value.

Dependency upgrades, especially Transformers/tokenizers, PyTorch/CUDA and
serialized scikit-learn models, need regression validation. Preserve old
environment manifests when introducing a separately validated environment.

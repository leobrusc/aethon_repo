# Authorization adversarial matrix

| Case | PR #28 behavior | PR #29 result | Evidence / note |
|---|---|---|---|
| Subclass `check()` returns `None` | ACCEPT: capability and run created | REJECT before backend call | Historical reproduction rerun on both code trees |
| Subclass `check()` returns `True` | Vulnerable virtual dispatch path | REJECT by exact-type check | `test_authorization_boundary.py`; CI |
| Subclass with matching fields | ACCEPT path did not require registry | REJECT | Exact type required |
| Manual base object, unregistered | Base `check()` rejects | REJECT | Direct negative tests and CI |
| Dataclass clone / equal-by-value | Not authority in base registry | REJECT | Direct negative tests and CI |
| Issued object with changed policy/receipt/launch/retention fields | No full snapshot check | REJECT | Snapshot tests use `object.__setattr__` |
| Different subject | REJECT | REJECT | Subject digest checked |
| Expired authorization | REJECT for use; owned close allowed | REJECT for use; cleanup allowed | Existing expiry/cleanup test and CI |
| Foreign or closed capability | REJECT | REJECT | Existing cross-backend/copy/close tests and CI |
| Legitimate `authorize()` fixture | ACCEPT | ACCEPT | Synthetic positive lifecycle in CI |
| Manual object registered via importable private issuer and token | Not applicable | **ACCEPT: capability/run created** | `tests/review_private_issuer_registration.py`, SHA-256 recorded in report |

The last row requires deliberate same-process access to underscore-prefixed implementation globals; it is not protection against an arbitrary compromised interpreter. It is still a demonstrated alternate emission route and violates the requirement that registration be exclusive to the gate-checked `authorize()` flow.

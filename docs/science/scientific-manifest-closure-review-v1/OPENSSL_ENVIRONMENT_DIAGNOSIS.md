# Legacy OpenSSL test environment diagnosis

## Local Windows sandbox attempt

The full local suite reached `tests/test_pilot_collector.py::test_production_ed25519_verifier_with_ephemeral_synthetic_key` and failed at its first `openssl genpkey` call, before key output or `OpenSSLVerifier` assertions. It is unrelated to `pilot_scientific_manifest`.

| Attribute | Observation |
|---|---|
| Executable selected | `C:\Program Files\Git\usr\bin\openssl.exe` (PATH lookup found no `openssl`; test used its Git for Windows fallback) |
| Static file version | OpenSSL 3.5.4; 1,003,388 bytes |
| Local executable SHA-256 | `2c6f2c64612cf45349f15850e4647b2fe594c2759de63a695ec4cbe13b2404da` |
| OS | Windows `10.0.26300.0` |
| Python | CPython 3.10.11 |
| Runner identity | Local non-administrator Python test process; Cygwin diagnostic child PID `7840` (Windows PID was not retained) |
| Spawn capability | `subprocess.Popen` created the child; it exited with `3221225794` (`0xC0000142`) |
| Failure | `openssl.exe: *** fatal error - couldn't create signal pipe, Win32 error 5` |
| Policy investigation | No AppLocker/EDR policy was queried or changed. No administrator execution, exclusion, or policy bypass was attempted. |

Local result: `ENVIRONMENT_BLOCKED`. This is not evidence of a failure in the new manifest validator and does not show a general inability to create subprocesses: the child started but Git for Windows could not initialize its Cygwin signal pipe in this sandbox. No signing key was generated.

## Approved compatible CI

Existing workflow run [#42322507843](https://github.com/leobrusc/aethon_repo/actions/runs/42322507843) is tied to PR head `2034aade…`; CI checked the PR merge ref `d0a44d9524ad1a05267b68d3d16287558090d701` (base #26 plus head #27). All three jobs completed `SUCCESS`. Windows Server 2025 / Python 3.12.10 reports **398 passed, 1 warning**; Linux reports **398 passed, 1 warning**. The OpenSSL test was part of that full, non-skipped suite, so it passed on the approved Windows runner. CI logs do not record that runner's OpenSSL path or hash; the local hash above must not be attributed to CI.

No separate isolated rerun was launched. The approved full-suite Windows CI is the successful execution evidence; local sandbox reproduction remains blocked. OpenSSL remains disabled as a production verifier backend.

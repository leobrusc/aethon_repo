# Native binary coverage

**COVERAGE_PARTIAL**. Four native extensions were read again from the acquired wheels and compared to selected quarantine copies; bounded PE/ELF inspection and preexisting GNU Binutils 2.46 readelf/objdump agree on visible imports. Tools never loaded the binaries; no ldd/dlopen/native execution. All four exact member hashes and full import/DT_NEEDED lists are in evidence/review.json and native-recheck.json.

| Platform/package | Member | SHA-256 | Coverage |
|---|---|---|---|
| windows-x86_64 / cryptography | `cryptography/hazmat/bindings/_rust.pyd` | `1d4332a447cab13dec8e3a533ad579e0e562b79e40822c931f33769758fc7156` | Static PE/ELF only |
| linux-x86_64 / cryptography | `cryptography/hazmat/bindings/_rust.abi3.so` | `f28d787117880abb13cc08822d1a0704d27e0fb33155d353f10a0a67efa6c4c1` | Static PE/ELF only |
| windows-x86_64 / cffi | `_cffi_backend.cp312-win_amd64.pyd` | `9af5e4f68a41f26b726f2e9424f9d58a4f5666189f6a48be95f406b257102aec` | Static PE/ELF only |
| linux-x86_64 / cffi | `_cffi_backend.cpython-312-x86_64-linux-gnu.so` | `9bc1d08072255a5ec2db10fc75df1dd9e73097a75cd9150cfe875ebd6712f17c` | Static PE/ELF only |

cryptography Windows/Linux: OpenSSL 4.0.3 (29 Sep 2026) is supported by literal strings and acquired embedded SBOM. Rust/PyO3 0.29.2, pyo3-ffi 0.29.2 and openssl-sys 0.9.117 have literal/SBOM evidence; rust-openssl crate 0.10.81 is declared. No standalone libcrypto/libssl import appears, consistent with upstream static-wheel design; precise linkage/options/backports are not independently established. No exact rustc toolchain identity is proven by a generic rustc marker.

cffi Windows/Linux: ffi/libffi symbols/references support presence, not release identity. **libffi version NOT_IDENTIFIED**. Upstream cffi v2.1.1 contains a separately licensed vendored libffi source tree, but that does not prove which source/commit produced the acquired wheel. pycparser has no native payload. OS imports (Windows CRT/kernel/network/crypto and Python DLLs; Linux libc, loader, pthread, dl/gcc as applicable) are names, not established deployed versions. No complete dynamic loader closure, native egress/sandbox guarantee or host-compromise resistance is claimed.

The 35 earlier exact queries were repeated: three PyPI package versions and 32 external crates, zero returned OSV advisories. Complete component/platform/date/status matrix: VULNERABILITY_COVERAGE.md and evidence/vulnerability-coverage.json. Official OpenSSL 4.0 advisory ranges reviewed separately; exact-bin coverage, unknown libffi and deployed OS library versions remain NOT_AUDITED. Build-only Rust declarations must not be counted as confirmed runtime components. No efficacy claims arise from synthetic tests.

**DEPENDENCY_APPROVAL_REQUIRED** remains for installation/locks/runtime/adapter. **PILOT_BLOCKED**, all eight operational gates PENDING. No installation, wheel/native import or execution, inference, runtime change, dependency/lock update or merge occurred.

# Validation: FlowSpeech SDK 0.2.1

Fresh local run on 2026-10-27 with Python 3.12.14. This section applies only
to the 0.2.1 candidates below; historical 0.2.0 results are preserved separately.

- Source suite: 220 passed.
- Fresh extracted-sdist suite: 220 passed.
- Installed-wheel suite with pytest source paths disabled: 220 passed.
- Installed import and distribution-metadata checks resolved to the fresh wheel
  target and confirmed version 0.2.1, not an editable or source checkout.
- Built a fresh sdist and built the wheel from that sdist using build 1.3.0 and
  hatchling 1.27.0. Twine 6.2.0 checks passed for both archives.
- Exact archive-member allowlists, wheel RECORD hashes, package/source byte
  equality, credential patterns, private paths, identity strings and public API
  terminology checks passed. No old active endpoint was found. Legacy URL
  literals in rejection tests were classified explicitly as negative fixtures.
- Tests used synthetic WAV data and mock transports; autouse fixtures blocked
  socket connections. No production calls, paid generation or credentials used.

## Candidate SHA-256

- dist/flowspeech_sdk-0.2.1-py3-none-any.whl:
  c315a11f00b4784d3ad9e0ce54d9faf0ab5a95e7ad4cca7ee341f9c085df0443
- dist/flowspeech_sdk-0.2.1.tar.gz:
  cbb17a44b5e5628a28e7eb3d143ebf8d098c0a85f02c9e305802c385afc1a6d5

Full commands, logs, member hashes and import proofs are in the coordinator's
verification-0_2_1-run3 evidence directory. python-handoff.json records final source
manifests and publication gates. Earlier failed local runs remain available as
diagnostic evidence, not as final validation. VALIDATION.md itself is deliberately
outside the sdist allowlist; README, CHANGELOG and RELEASE instructions are included.

## Remaining Gates

No commit, push, tag, workflow dispatch or publication was performed. The coordinator
must authorize each remote write separately, confirm registry availability, review
workflow trigger and artifact-consistency risks, verify final source/artifact hashes,
and obtain passing remote CI for supported Python versions. Local execution covered
Python 3.12 only. Do not infer remote CI or publication success from these checks.

# Historical Validation: 0.2.0

The record below is preserved verbatim and is not evidence for 0.2.1.

# Validation: FlowSpeech SDK 0.2.0

2026-10-26, Python 3.12.14. No paid generation or production credentials used.

- Source tests: 179 passed, including independent-review regressions for storage
  error classification, supplied recovery IDs, validated result URLs and text trimming.
- Built sdist and wheel from sdist with build 1.3.0 and hatchling 1.27.0.
- Twine 6.2.0 metadata checks passed for both artifacts.
- Installed the wheel and reran all 179 tests with pytest's source path disabled.
- Package member and credential-pattern audit passed; no caches, local paths,
  environment files or credentials were included.
- Shared adapter and contract tests come from the hardened CLI/LangChain v1 adapter.
- Public 0.1.0 synthesis and exception imports are retained; API-key requirements,
  dependency changes and result metadata are documented in README.

Final publication requires coordinator review and passing remote CI. This file
records local checks and is not evidence of a PyPI release. Tests use fake HTTP
transports and valid synthetic WAV files. Socket connections are blocked in tests.

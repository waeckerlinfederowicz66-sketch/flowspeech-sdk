# Validation: FlowSpeech SDK 0.2.0

2026-10-26, Python 3.12.14. No paid generation or production credentials used.

- Source tests: 171 passed.
- Built sdist and wheel from sdist with build 1.3.0 and hatchling 1.27.0.
- Twine 6.2.0 metadata checks passed for both artifacts.
- Installed the wheel and reran all 171 tests with pytest's source path disabled.
- Package member and credential-pattern audit passed; no caches, local paths,
  environment files or credentials were included.
- Shared adapter and contract tests come from the hardened CLI/LangChain v1 adapter.
- Public 0.1.0 synthesis and exception imports are retained; API-key requirements,
  dependency changes and result metadata are documented in README.

Final publication requires coordinator review and passing remote CI. This file
records local checks and is not evidence of a PyPI release. Tests use fake HTTP
transports and valid synthetic WAV files. Socket connections are blocked in tests.

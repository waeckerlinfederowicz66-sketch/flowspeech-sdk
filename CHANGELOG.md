# Changelog

## 0.2.1 - 2026-10-27

- Keep reflected credentials and private URLs out of error messages, codes and
  trace IDs, including terminal-job errors.
- Preserve HTTP status and Retry-After when a response body is interrupted;
  do not retry known authentication failures.
- Bound active HTTP workers and reject overlapping calls on an occupied client,
  including requests that remain active after the caller's deadline.

## 0.2.0

- Migrate to authenticated public API v1 jobs, quota and voices.
- Add stable request IDs, recovery, cancellation, multi-speaker input and separate downloads.
- Preserve the synchronous synthesis result and exception imports.
- Validate complete WAV data and isolate storage requests from API credentials.
- Add source and installed-package contract tests.

## 0.1.0

- Initial Python client.

# Release 0.2.1

This candidate contains the previously reviewed FlowSpeech public API v1 safety
fixes: sanitized upstream errors, interrupted-body status/cooldown preservation,
and bounded HTTP-worker lifetimes. No additional API behavior is introduced.

Only the coordinator may commit, tag, push, dispatch publication workflows, or
publish packages, after separate authorization. Preserve all older releases and
tags. Use commit email waeckerlinfederowicz66@gmail.com for a future authorized commit.

## Local Verification

Run source tests with synthetic audio and mock transports only. Build fresh
0.2.1 wheels and sdists with build 1.3.0 and hatchling 1.27.0, then run twine 6.2.0
checks. Test the extracted sdist and install the actual wheel into a fresh target;
disable pytest's source path and verify imports resolve to that installed target.
Inspect every archive member against an explicit allowlist, scan actual contents,
and record final SHA-256 hashes. Do not reuse historical 0.2.0 test evidence.

Current local results are in the 0.2.1 section of VALIDATION.md. Exact candidate
hashes, logs, changed files and remaining gates are in the coordinator's
python-handoff.json for this release.

## Publication Gates

Confirm 0.2.1 registry availability, final committed source, passing remote CI,
and exact artifact hashes before any publication. No production key, paid
generation, credential files, local runtimes, caches or private paths belong in
the distributions.

The existing publish workflow can run on a published release or manual dispatch.
Its publish job rebuilds independently after verification, so the coordinator
must address verified-versus-uploaded artifact consistency before using it.
Do not dispatch that workflow as a test.

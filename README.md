# FlowSpeech Python SDK

Python 3.12+ client for the [FlowSpeech public API](https://flowspeech.io/docs/public-api).
An active paid Basic, Pro or Scale subscription and a developer API key are required.
Trial access does not include API generation. Generation consumes account credits.

```sh
pip install flowspeech-sdk==0.2.0
export FLOWSPEECH_API_KEY='YOUR_FLOWSPEECH_API_KEY'
```

```python
from pathlib import Path
from uuid import uuid4
from flowspeech_sdk import FlowSpeechClient, FlowSpeechError

request_id = str(uuid4())  # Persist this before submission; reuse it for the same input.
print("Recovery request ID:", request_id)
with FlowSpeechClient(timeout=300) as client:
    print(client.get_account())  # Read-only quota, subscription and limits.
    try:
        result = client.synthesize("Hello from FlowSpeech", voice="Kore", request_id=request_id)
        with Path("speech.wav").open("xb") as output:
            output.write(result.audio)
    except FlowSpeechError as error:
        print(error.code, error.request_id, error.job_id)
        raise
```

Calls are blocking. Async applications should schedule them in a worker thread.
Never place the API key in browser code or publish it in logs or source files.

## Recovery and Multi-Speaker Audio

Use `find_job(request_id)` after a lost response, `get_job(job_id)` to check status,
and `download(job_id)` to retrieve an existing successful recording. A download
retry does not create another recording. `cancel_job(job_id)` explicitly requests
cancellation; a local timeout does not automatically cancel remote work.

```python
segments = [
    {"speaker": "Alice", "text": "Welcome.", "voiceName": "Kore"},
    {"speaker": "Bob", "text": "Thank you.", "voiceName": "Puck"},
]
with FlowSpeechClient() as client:
    result = client.synthesize_multi(segments, request_id=str(uuid4()))
```

Supply a caller-persisted UUID for robust recovery even if the process is stopped.
Retries preserve the same UUID and serialized input. Polling waits at least five
seconds and honors longer server cooldowns. The configurable total deadline
includes HTTP requests, polling and audio download; it defaults to 120 seconds.

A deadline ends local waiting, not the remote job. A transport already in progress
may finish later; its worker performs no follow-up request. Each client permits
one active HTTP request, and this package permits at most eight HTTP workers per
process. An occupied client raises `request_in_progress`; exhausted capacity
raises `client_busy`, without queueing or sending another request. Do not use one
client concurrently, and recover the original request ID after a timeout instead
of submitting a new recording. Caller-owned HTTP clients are never closed.
Closing this client rejects future work; cleanup of owned HTTP clients is
deferred until any active request exits, rather than blocking local shutdown.

If reading a response body fails, known status codes and Retry-After are retained.
Authentication failures are not retried. Interrupted successful or server-error
responses use bounded transport retries with the original UUID and body.
Errors use a local HTTP-status message rather than echoing upstream text. Error
codes and trace IDs are bounded tokens, filtered for credentials and URLs;
request/job IDs remain available for recovery.

## Migration from 0.1.0

- API keys are required, either explicitly or through `FLOWSPEECH_API_KEY`.
- `synthesize(text, voice=...)` and the `SynthesisResult.audio` bytes remain.
- Calls use `/api/v1/tts/jobs` with submit, poll and separate download operations.
- `get_quota()` keeps its quota-only mapping; `get_account()` includes subscription and limits.
- Output is validated PCM WAV, 24 kHz, mono, 16-bit. MP3, model and speed options are unsupported.
- `quota` on a synthesis result remains `None`; billing is available as `usage`.
- This release adds an `httpx` dependency. Custom API URLs must use HTTPS and the v1 paths.
- Error types retain request/job IDs and structured codes for recovery.

API redirects are rejected. Audio downloads use a separate credential-free
request, validate HTTPS redirects, enforce a 64 MiB bound and validate the WAV
container. A deleted result is reported explicitly. No API credentials or cookies
are sent to audio storage.

## Development

```sh
pip install -e '.[test]'
pytest -q
python -m build
```

Tests use synthetic audio and mock HTTP transports. They do not generate paid audio.

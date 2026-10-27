"""Synchronous FlowSpeech public API v1 client."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit

from ._v1 import ApiError, V1Client, identifier, make_input, safe_url

DEFAULT_API_URL = "https://flowspeech.io/api/v1/tts/jobs"
DEFAULT_QUOTA_URL = "https://flowspeech.io/api/v1/quota"
DEFAULT_VOICE = "Kore"
USER_AGENT = "flowspeech-sdk/0.2.1"
FlowSpeechError = ApiError


class FlowSpeechAuthError(FlowSpeechError):
    """FlowSpeech rejected the credentials or subscription."""


class FlowSpeechRateLimitError(FlowSpeechError):
    """FlowSpeech rate limited the request after bounded retries."""


class FlowSpeechConnectionError(FlowSpeechError):
    """Transport failure or deadline; retain recovery identifiers."""


@dataclass(frozen=True)
class SynthesisResult:
    audio: bytes
    audio_format: str = "wav"
    mime_type: str = "audio/wav"
    sample_rate: int = 24000
    num_channels: int = 1
    bits_per_sample: int = 16
    quota: dict[str, Any] | None = None
    request_id: str | None = None
    job_id: str | None = None
    result_url: str | None = None
    usage: dict[str, Any] | None = None


class FlowSpeechClient:
    """Blocking client; schedule calls off an async application's event loop."""

    def __init__(self, *, api_key: str | None = None,
                 api_url: str = DEFAULT_API_URL, quota_url: str | None = None,
                 timeout: float = 120, retries: int = 2) -> None:
        safe_url(api_url)
        parsed = urlsplit(api_url)
        if parsed.path != "/api/v1/tts/jobs" or parsed.query:
            raise ValueError("api_url must use /api/v1/tts/jobs without a query")
        origin = f"{parsed.scheme}://{parsed.netloc}"
        if quota_url is not None and quota_url != origin + "/api/v1/quota":
            raise ValueError("quota_url must use the same origin and /api/v1/quota")
        self.api_url, self.quota_url = api_url, origin + "/api/v1/quota"
        self.timeout, self.retries = timeout, retries
        self._client = V1Client(api_key=api_key, base_url=origin, timeout=timeout,
                                max_retries=retries, user_agent=USER_AGENT)

    def close(self) -> None:
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    @staticmethod
    def _call(operation, *args, _request_id=None, _job_id=None, _result_url=None, **kwargs):
        try:
            return operation(*args, **kwargs)
        except ApiError as error:
            category = (
                FlowSpeechConnectionError if error.code == "download_failed" else
                FlowSpeechAuthError if error.status_code in (401, 403) else
                FlowSpeechRateLimitError if error.status_code == 429 else
                FlowSpeechConnectionError if error.code in
                ("transport_error", "deadline_exceeded", "download_failed") else FlowSpeechError
            )
            raise category(str(error), status_code=error.status_code, code=error.code,
                           retryable=error.retryable, trace_id=error.trace_id,
                           request_id=error.request_id or _request_id,
                           job_id=error.job_id or _job_id,
                           result_url=error.result_url or _result_url) from None

    def get_account(self) -> dict[str, Any]:
        """Return quota, subscription and limits without creating a recording."""
        return self._call(self._client.quota)

    def get_quota(self) -> dict[str, Any]:
        """Preserve the original method's quota-only return shape."""
        return self.get_account()["quota"]

    def get_voices(self) -> list[dict[str, Any]]:
        return self._call(self._client.voices)

    def get_job(self, job_id: str) -> dict[str, Any]:
        job_id = identifier(job_id)
        return self._call(self._client.get_job, job_id, _job_id=job_id)

    def find_job(self, request_id: str) -> dict[str, Any]:
        request_id = identifier(request_id)
        return self._call(self._client.find_job, request_id, _request_id=request_id)

    def cancel_job(self, job_id: str) -> dict[str, Any]:
        job_id = identifier(job_id)
        return self._call(self._client.cancel_job, job_id, _job_id=job_id)

    @staticmethod
    def _result(job, audio) -> SynthesisResult:
        return SynthesisResult(audio=audio, request_id=job["requestId"], job_id=job["id"],
                               result_url=job["result"]["url"], usage=job["usage"])

    def synthesize(self, text: str, *, voice: str = DEFAULT_VOICE,
                   request_id: str | None = None) -> SynthesisResult:
        """Submit, poll and download; supply a persisted UUID for recovery."""
        if isinstance(text, str):
            text = text.strip()
        job, audio, _ = self._call(self._client.generate, make_input(text, voice),
                                  request_id=request_id)
        return self._result(job, audio)

    def synthesize_multi(self, segments: list[dict[str, str]], *,
                         request_id: str | None = None) -> SynthesisResult:
        job, audio, _ = self._call(self._client.generate, make_input(segments=segments),
                                  request_id=request_id)
        return self._result(job, audio)

    def download(self, job_id: str) -> SynthesisResult:
        """Download an existing successful recording; never submit a new job."""
        job_id = identifier(job_id)
        deadline = self._client.clock() + self._client.timeout
        job = self._call(self._client.get_job, job_id, deadline=deadline, _job_id=job_id)
        result_url = None
        if isinstance(job.get("result"), dict):
            try:
                result_url = safe_url(job["result"].get("url"))
            except ValueError:
                pass
        try:
            if job["status"] != "success":
                raise ApiError("Job is not successful", code=job["status"])
            result = self._client._result(job)
            result_url = result["url"]
            audio = self._call(self._client.download_audio, result["url"], deadline=deadline)
            return self._result(job, audio)
        except ApiError as error:
            error.request_id, error.job_id = job["requestId"], job["id"]
            error.result_url = error.result_url or result_url
            raise

import json

import httpx
import pytest

from flowspeech_sdk import (
    FlowSpeechClient, FlowSpeechError, FlowSpeechAuthError,
    FlowSpeechRateLimitError, FlowSpeechConnectionError,
)
from flowspeech_sdk._v1 import ApiError
from test_v1_contract import factory, job, response, wav_bytes, JOB, REQUEST, INPUT


def wrap(monkeypatch, client):
    monkeypatch.setattr("flowspeech_sdk.client.V1Client", lambda **kwargs: client)
    return FlowSpeechClient(api_key="test-only")


def test_synthesize_retains_public_result(monkeypatch, factory):
    adapter, calls, downloads, _ = factory([response(job())])
    with wrap(monkeypatch, adapter) as sdk:
        result = sdk.synthesize("Hello", request_id=REQUEST)
    assert result.audio == wav_bytes()
    assert (result.audio_format, result.mime_type, result.sample_rate,
            result.num_channels, result.bits_per_sample) == ("wav", "audio/wav", 24000, 1, 16)
    assert result.job_id == JOB and result.request_id == REQUEST
    assert result.usage == job()["usage"] and result.quota is None
    assert json.loads(calls[0].content) == {"input": INPUT}
    assert "authorization" not in downloads[0].headers


def test_multi(monkeypatch, factory):
    adapter, calls, _, _ = factory([response(job())])
    segments = [{"speaker": "Alice", "text": "Hello", "voiceName": "Kore"}]
    sdk = wrap(monkeypatch, adapter)
    assert sdk.synthesize_multi(segments, request_id=REQUEST).job_id == JOB
    assert json.loads(calls[0].content)["input"] == {"mode": "multi", "segments": segments}


def test_read_methods(monkeypatch, factory):
    account = {"quota": {"remaining": 10, "reserved": 0, "available": 10},
               "subscription": {"plan": "basic"}, "limits": {}}
    voices = [{"name": "Kore"}]
    adapter, calls, _, _ = factory([response(account), response(account),
                                   response({"voices": voices}), response(job()),
                                   response(job()), response(job("cancelled"))])
    sdk = wrap(monkeypatch, adapter)
    assert sdk.get_account() == account
    assert sdk.get_quota() == account["quota"]
    assert sdk.get_voices() == voices
    assert sdk.find_job(REQUEST)["id"] == JOB
    assert sdk.get_job(JOB)["id"] == JOB
    assert sdk.cancel_job(JOB)["status"] == "cancelled"
    assert calls[-1].url.path.endswith("/cancel")


def test_download_does_not_create(monkeypatch, factory):
    adapter, calls, _, _ = factory([response(job())])
    sdk = wrap(monkeypatch, adapter)
    assert sdk.download(JOB).audio == wav_bytes()
    assert len(calls) == 1 and calls[0].method == "GET"


@pytest.mark.parametrize("status", ["queued", "failed", "cancelled"])
def test_download_requires_success(monkeypatch, factory, status):
    adapter, calls, downloads, _ = factory([response(job(status))])
    sdk = wrap(monkeypatch, adapter)
    with pytest.raises(FlowSpeechError) as caught:
        sdk.download(JOB)
    assert caught.value.job_id == JOB and caught.value.request_id == REQUEST
    assert not downloads and all(c.method == "GET" for c in calls)


@pytest.mark.parametrize("http_status,code,expected", [
    (401, "unauthorized", FlowSpeechAuthError),
    (403, "forbidden", FlowSpeechAuthError),
    (429, "rate_limited", FlowSpeechRateLimitError),
    (None, "deadline_exceeded", FlowSpeechConnectionError),
    (400, "invalid_request", FlowSpeechError),
])
def test_error_mapping_keeps_recovery_ids(http_status, code, expected):
    def fail():
        raise ApiError("Failure", status_code=http_status, code=code,
                       trace_id="trace", request_id=REQUEST, job_id=JOB)
    with pytest.raises(expected) as caught:
        FlowSpeechClient._call(fail)
    assert caught.value.request_id == REQUEST and caught.value.job_id == JOB
    assert caught.value.trace_id == "trace" and caught.value.code == code


@pytest.mark.parametrize("kwargs", [
    {"api_url": "https://flowspeech.io/api/ai/text-to-speech"},
    {"api_url": "http://flowspeech.io/api/v1/tts/jobs"},
    {"api_url": "https://user:pass@flowspeech.io/api/v1/tts/jobs"},
    {"quota_url": "https://elsewhere.example/api/v1/quota"},
])
def test_bad_config_fails_before_client(monkeypatch, kwargs):
    def forbidden(**options):
        pytest.fail("invalid configuration constructed a client")
    monkeypatch.setattr("flowspeech_sdk.client.V1Client", forbidden)
    with pytest.raises(ValueError):
        FlowSpeechClient(**kwargs)


def test_invalid_text_and_unsupported_options_no_requests(monkeypatch, factory):
    adapter, calls, _, _ = factory([])
    sdk = wrap(monkeypatch, adapter)
    with pytest.raises(ValueError):
        sdk.synthesize(" ")
    with pytest.raises(TypeError):
        sdk.synthesize("Hello", speed=2)
    assert not calls


def test_environment_key(monkeypatch):
    monkeypatch.setenv("FLOWSPEECH_API_KEY", "test-only")
    with FlowSpeechClient() as sdk:
        assert sdk._client.api_key == "test-only"
    monkeypatch.delenv("FLOWSPEECH_API_KEY")
    with pytest.raises(FlowSpeechError):
        FlowSpeechClient()


@pytest.mark.parametrize("method,value,expected_field", [
    ("get_job", JOB, "job_id"),
    ("find_job", REQUEST, "request_id"),
    ("cancel_job", JOB, "job_id"),
    ("download", JOB, "job_id"),
])
def test_lookup_transport_failure_preserves_supplied_id(monkeypatch, factory, method, value, expected_field):
    adapter, calls, _, _ = factory([httpx.ConnectError("offline")], max_retries=0)
    sdk = wrap(monkeypatch, adapter)
    with pytest.raises(FlowSpeechError) as caught:
        getattr(sdk, method)(value)
    assert getattr(caught.value, expected_field) == value
    assert len(calls) == 1


@pytest.mark.parametrize("status", [401, 403])
def test_storage_auth_failure_is_not_api_auth_failure(monkeypatch, factory, status):
    adapter, _, _, _ = factory([response(job())], [httpx.Response(status, text="denied")])
    sdk = wrap(monkeypatch, adapter)
    with pytest.raises(FlowSpeechConnectionError) as caught:
        sdk.synthesize("Hello", request_id=REQUEST)
    assert not isinstance(caught.value, FlowSpeechAuthError)
    assert caught.value.code == "download_failed"
    assert caught.value.request_id == REQUEST and caught.value.job_id == JOB
    assert caught.value.result_url == job()["result"]["url"]


def test_download_metadata_failure_keeps_safe_url(monkeypatch, factory):
    broken = job()
    broken["result"]["sampleRate"] = 8000
    adapter, _, downloads, _ = factory([response(broken)])
    sdk = wrap(monkeypatch, adapter)
    with pytest.raises(FlowSpeechError) as caught:
        sdk.download(JOB)
    assert caught.value.request_id == REQUEST and caught.value.job_id == JOB
    assert caught.value.result_url == broken["result"]["url"]
    assert not downloads


def test_text_whitespace_compatibility(monkeypatch, factory):
    adapter, calls, _, _ = factory([response(job())])
    sdk = wrap(monkeypatch, adapter)
    sdk.synthesize("  Hello  ", request_id=REQUEST)
    assert json.loads(calls[0].content)["input"]["text"] == "Hello"

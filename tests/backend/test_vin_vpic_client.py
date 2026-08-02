"""Tests for the NHTSA vPIC HTTP client -- network is always mocked via respx."""

from __future__ import annotations

import httpx
import respx

from backend.app.vin.vpic_client import _VPIC_BASE_URL, VpicClient

VIN = "1HGCM82633A004352"


@respx.mock
def test_decode_vin_returns_first_result_on_success() -> None:
    respx.get(f"{_VPIC_BASE_URL}/{VIN}").mock(
        return_value=httpx.Response(200, json={"Results": [{"Make": "HONDA", "Model": "Accord"}]})
    )
    client = VpicClient()
    result = client.decode_vin(VIN)
    assert result == {"Make": "HONDA", "Model": "Accord"}


@respx.mock
def test_decode_vin_returns_none_on_timeout() -> None:
    respx.get(f"{_VPIC_BASE_URL}/{VIN}").mock(side_effect=httpx.TimeoutException("timed out"))
    client = VpicClient(timeout_seconds=0.5)
    assert client.decode_vin(VIN) is None


@respx.mock
def test_decode_vin_returns_none_on_connection_error() -> None:
    respx.get(f"{_VPIC_BASE_URL}/{VIN}").mock(side_effect=httpx.ConnectError("no network"))
    client = VpicClient()
    assert client.decode_vin(VIN) is None


@respx.mock
def test_decode_vin_returns_none_on_http_error_status() -> None:
    respx.get(f"{_VPIC_BASE_URL}/{VIN}").mock(return_value=httpx.Response(500))
    client = VpicClient()
    assert client.decode_vin(VIN) is None


@respx.mock
def test_decode_vin_returns_none_on_malformed_json() -> None:
    respx.get(f"{_VPIC_BASE_URL}/{VIN}").mock(return_value=httpx.Response(200, content=b"not json"))
    client = VpicClient()
    assert client.decode_vin(VIN) is None


@respx.mock
def test_decode_vin_returns_none_on_empty_results() -> None:
    respx.get(f"{_VPIC_BASE_URL}/{VIN}").mock(
        return_value=httpx.Response(200, json={"Results": []})
    )
    client = VpicClient()
    assert client.decode_vin(VIN) is None

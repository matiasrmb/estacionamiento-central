"""Cliente HTTP mínimo para las operaciones centralizadas de la API."""

import json
from configparser import ConfigParser
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from utils.db import get_base_paths


class ApiClientError(RuntimeError):
    def __init__(self, status=None, detail=None):
        super().__init__(detail or "API_REQUEST_FAILED")
        self.status = status
        self.detail = detail


def _api_base_url():
    config = ConfigParser()
    for base_path in get_base_paths():
        config_path = f"{base_path}/config.ini"
        if not config.read(config_path, encoding="utf-8"):
            continue
        if config.has_option("api", "base_url"):
            return config.get("api", "base_url").rstrip("/")
    return "http://localhost:8000/api/v1"


def _request(method, path, payload=None, token=None):
    base_url = _api_base_url()
    if not base_url:
        raise ApiClientError(detail="API_NOT_CONFIGURED")

    headers = {"Accept": "application/json"}
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = Request(f"{base_url}{path}", data=data, headers=headers, method=method)
    try:
        with urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        try:
            detail = json.loads(detail).get("detail", detail)
        except json.JSONDecodeError:
            pass
        raise ApiClientError(status=exc.code, detail=str(detail)) from exc
    except json.JSONDecodeError as exc:
        raise ApiClientError(detail="API_INVALID_RESPONSE") from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise ApiClientError(detail="API_UNAVAILABLE") from exc


def autenticar(usuario, clave):
    response = _request(
        "POST",
        "/auth/login",
        {"usuario": usuario, "clave": clave},
    )
    if not response.get("access_token"):
        raise ApiClientError(detail="API_INVALID_RESPONSE")
    return response


def crear_cierre(token):
    return _request("POST", "/cierres", token=token)

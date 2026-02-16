from __future__ import annotations

import httpx
from dataclasses import dataclass, field
from typing import Any

from .errors import APIError, Unauthorized, Forbidden, NotFound, RateLimited
from .retry import RetryPolicy
from .auth.base import AuthStrategy

Json = dict[str, Any]

@dataclass
class APIClient:
    base_url: str
    auth: AuthStrategy | None = None
    timeout_s: float = 15.0
    retry: RetryPolicy = field(default_factory=RetryPolicy)
    default_headers: dict[str, str] = field(default_factory=dict)

    def _build_headers(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        headers = {"Accept": "application/json", **self.default_headers}
        if extra:
            headers.update(extra)
        if self.auth:
            self.auth.apply(headers)
        return headers

    def _request(self, method: str, path: str, *, params=None, json=None, headers=None) -> httpx.Response:
        url = self.base_url.rstrip("/") + "/" + path.lstrip("/")
        last_exc: Exception | None = None

        for attempt in range(1, self.retry.max_attempts + 1):
            try:
                with httpx.Client(timeout=self.timeout_s) as client:
                    resp = client.request(
                        method=method,
                        url=url,
                        params=params,
                        json=json,
                        headers=self._build_headers(headers),
                    )
                if resp.status_code == 429:
                    retry_after = resp.headers.get("Retry-After")
                    ra = float(retry_after) if retry_after and retry_after.isdigit() else None
                    raise RateLimited(429, "Rate limited", retry_after=ra, payload=self._safe_json(resp))

                if 500 <= resp.status_code <= 599:
                    raise APIError(resp.status_code, "Server error", payload=self._safe_json(resp))

                return resp

            except RateLimited as e:
                last_exc = e
                if e.retry_after is not None:
                    import time
                    time.sleep(e.retry_after)
                elif attempt < self.retry.max_attempts:
                    self.retry.backoff_sleep(attempt)
                else:
                    raise

            except (httpx.TimeoutException, httpx.TransportError, APIError) as exc:
                last_exc = exc
                if attempt < self.retry.max_attempts:
                    self.retry.backoff_sleep(attempt)
                else:
                    raise

        if last_exc:
            raise last_exc
        raise RuntimeError("Request failed with unknown error")

    def _raise_for_status(self, resp: httpx.Response) -> None:
        if resp.status_code < 400:
            return
        payload = self._safe_json(resp)
        msg = (payload.get("message") if isinstance(payload, dict) else None) or resp.text or "Unknown error"

        if resp.status_code == 401:
            raise Unauthorized(401, msg, payload=payload)
        if resp.status_code == 403:
            raise Forbidden(403, msg, payload=payload)
        if resp.status_code == 404:
            raise NotFound(404, msg, payload=payload)
        raise APIError(resp.status_code, msg, payload=payload)

    @staticmethod
    def _safe_json(resp: httpx.Response):
        try:
            return resp.json()
        except Exception:
            return None

    # Public helpers
    def get_json(self, path: str, *, params: dict[str, Any] | None = None) -> Json:
        resp = self._request("GET", path, params=params)
        self._raise_for_status(resp)
        return resp.json()

    def post_json(self, path: str, *, json_body: dict[str, Any]) -> Json:
        resp = self._request("POST", path, json=json_body)
        self._raise_for_status(resp)
        return resp.json()

    def paginate_page(self, path: str, *, params: dict[str, Any] | None = None, items_path: str = "data",
                      per_page: int = 50, max_pages: int | None = None):
        from .pagination.page import PagePagination

        paginator = PagePagination(items_path=items_path, per_page=per_page)

        def fetch(p: dict[str, Any]):
            return self.get_json(path, params=p)

        yield from paginator.iterate(fetch, params=params, max_pages=max_pages)

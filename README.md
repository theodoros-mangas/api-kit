# api-kit
An api-client kit with auth strategies, pagination and error handling and more
# api-client-kit

A small but production-oriented Python library for building reliable API clients.

> Most API wrappers online are thin request helpers.
> This project demonstrates how to design a reusable client with retries, authentication strategies, pagination helpers and clear error handling.

The goal is not to wrap a specific API — but to provide a **clean foundation** for integrating *any* REST service.

---

## Why this exists

Typical API usage in many projects:

```python
requests.get(url).json()
```

Real systems need more:

* retries & exponential backoff
* authentication strategies
* rate-limit handling
* pagination helpers
* predictable error types
* testability without network

This repository shows how to structure that cleanly.

---

## Features

* Retry policy (timeouts, 429, 5xx)
* Pluggable authentication (Token, Basic, OAuth-style)
* Structured exceptions (`Unauthorized`, `NotFound`, `RateLimited`)
* Page-based pagination helper
* Minimal dependencies (`httpx` only)
* Unit-test friendly design

---

## Installation

```bash
git clone <repo-url>
cd api-client-kit

python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install -e ".[dev]"
```

Verify:

```bash
python -c "import api_client_kit; print('ok')"
```

---

## Basic Usage

```python
from api_client_kit import APIClient
from api_client_kit.auth import TokenAuth

client = APIClient(
    base_url="https://api.example.com",
    auth=TokenAuth("MY_TOKEN"),
)

user = client.get_json("/users/123")
print(user)
```

---

## Pagination

Many APIs use `?page=` or `?per_page=` parameters.
The library provides an iterator so you don't manually loop pages.

```python
for item in client.paginate_page(
        "/items",
        params={"status": "active"},
        items_path="data",
        per_page=50
    ):
    print(item)
```

The iterator stops automatically when no more data exists.

---

## Authentication Strategies

### Bearer token

```python
from api_client_kit.auth import TokenAuth
client = APIClient(base_url=URL, auth=TokenAuth("TOKEN"))
```

### Basic auth

```python
from api_client_kit.auth import BasicAuth
client = APIClient(base_url=URL, auth=BasicAuth("user", "pass"))
```

Custom strategies can be created by implementing:

```python
class AuthStrategy:
    def apply(self, headers: dict[str, str]) -> None:
        ...
```

---

## Error Handling

The client raises structured exceptions instead of raw HTTP responses.

```python
from api_client_kit.errors import NotFound, RateLimited

try:
    client.get_json("/users/999")
except NotFound:
    print("User does not exist")
except RateLimited as e:
    print("Retry after:", e.retry_after)
```

---

## Retry Behaviour

Automatic retries occur for:

* timeouts
* connection errors
* HTTP 429
* HTTP 5xx

Using exponential backoff with jitter.

---

## Testing

The client is designed to be testable without internet access.

```
pytest -q
```

Tests mock HTTP responses rather than hitting real APIs.

---

## Architecture

```
APIClient
 ├─ Auth Strategy
 ├─ Retry Policy
 ├─ HTTP Transport (httpx)
 ├─ Pagination Helpers
 └─ Structured Errors
```

Site-specific logic should live outside the client — the library remains reusable.

---

## Example Use Cases

* building internal service SDKs
* integrating third-party APIs
* data ingestion pipelines
* webhook consumers
* microservices communication

---

## License

MIT

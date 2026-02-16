from __future__ import annotations
import base64
from dataclasses import dataclass
from .base import AuthStrategy

@dataclass(frozen=True)
class BasicAuth(AuthStrategy):
    username: str
    password: str

    def apply(self, headers: dict[str, str]) -> None:
        raw = f"{self.username}:{self.password}".encode("utf-8")
        headers["Authorization"] = "Basic " + base64.b64encode(raw).decode("ascii")

from __future__ import annotations
from dataclasses import dataclass
from .base import AuthStrategy

@dataclass(frozen=True)
class TokenAuth(AuthStrategy):
    token: str
    scheme: str = "Bearer"

    def apply(self, headers: dict[str, str]) -> None:
        headers["Authorization"] = f"{self.scheme} {self.token}"

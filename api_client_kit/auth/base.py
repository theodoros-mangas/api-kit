from __future__ import annotations
from abc import ABC, abstractmethod

class AuthStrategy(ABC):
    @abstractmethod
    def apply(self, headers: dict[str, str]) -> None:
        """Mutate headers in-place."""
        raise NotImplementedError

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable, Iterator, Optional

from cnpj_extractor.models import CompanyEmail


ProgressCallback = Optional[Callable[[float, str], None]]


class BaseSource(ABC):
    name: str
    description: str

    @abstractmethod
    def extract(self, **kwargs) -> Iterator[CompanyEmail]:
        raise NotImplementedError

    def _report(self, callback: ProgressCallback, value: float, message: str) -> None:
        if callback:
            callback(min(max(value, 0.0), 1.0), message)

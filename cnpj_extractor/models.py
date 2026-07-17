from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class CompanyEmail:
    cnpj: str
    email: str
    razao_social: str = ""
    nome_fantasia: str = ""
    telefone: str = ""
    uf: str = ""
    municipio: str = ""
    cnae: str = ""
    situacao: str = ""
    fonte: str = ""
    data_extracao: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

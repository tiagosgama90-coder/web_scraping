from __future__ import annotations

import json
import os
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

SOURCE_TYPES = {
    "sitemap": "Sitemap XML (descobre páginas automaticamente)",
    "urls": "Lista de URLs (colar links manualmente)",
    "pagina": "Página única ou site (extrai e-mails da página)",
}


def get_config_dir() -> Path:
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:
        base = Path.home() / ".local" / "share"
    path = base / "CompanyEmailExtractor"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_sources_file() -> Path:
    return get_config_dir() / "custom_sources.json"


@dataclass
class CustomSource:
    id: str
    name: str
    url: str
    source_type: str  # sitemap | urls | pagina
    country: str = "OUTRO"
    auto_discover: bool = True
    url_list: str = ""
    notes: str = ""
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> CustomSource:
        return cls(
            id=data.get("id", str(uuid.uuid4())[:8]),
            name=data.get("name", "Fonte personalizada"),
            url=data.get("url", ""),
            source_type=data.get("source_type", "sitemap"),
            country=data.get("country", "OUTRO"),
            auto_discover=data.get("auto_discover", True),
            url_list=data.get("url_list", ""),
            notes=data.get("notes", ""),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
        )


def load_custom_sources() -> list[CustomSource]:
    path = get_sources_file()
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return [CustomSource.from_dict(item) for item in data]
    except (json.JSONDecodeError, OSError):
        return []


def save_custom_sources(sources: list[CustomSource]) -> None:
    path = get_sources_file()
    payload = [s.to_dict() for s in sources]
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def add_custom_source(source: CustomSource) -> CustomSource:
    sources = load_custom_sources()
    if not source.id:
        source.id = str(uuid.uuid4())[:8]
    sources.append(source)
    save_custom_sources(sources)
    return source


def delete_custom_source(source_id: str) -> bool:
    sources = load_custom_sources()
    new_list = [s for s in sources if s.id != source_id]
    if len(new_list) == len(sources):
        return False
    save_custom_sources(new_list)
    return True


def get_custom_source(source_id: str) -> CustomSource | None:
    for source in load_custom_sources():
        if source.id == source_id:
            return source
    return None


def parse_url_list(text: str) -> list[str]:
    urls: list[str] = []
    seen: set[str] = set()
    for line in (text or "").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "," in line and not line.startswith("http"):
            parts = line.split(",")
            for part in parts:
                part = part.strip()
                if part.startswith("http") and part not in seen:
                    seen.add(part)
                    urls.append(part)
            continue
        if line.startswith("http") and line not in seen:
            seen.add(line)
            urls.append(line)
    return urls

from __future__ import annotations

import time
from typing import Iterator

import requests

from cnpj_extractor.models import CompanyEmail
from cnpj_extractor.sources.base import BaseSource, ProgressCallback
from cnpj_extractor.utils import (
    clean_cnpj,
    format_phone,
    is_valid_email,
    normalize_email,
    normalize_situacao,
)

API_BASE = "https://api.dadosbrasil.net/api/v1"


class DadosBrasilApiSource(BaseSource):
    name = "DadosBrasil API"
    description = (
        "API pública gratuita com dados da Receita Federal. Ideal para consultas "
        "filtradas por UF, CNAE ou lista de CNPJs."
    )

    def __init__(self, delay_seconds: float = 0.15):
        self.delay_seconds = delay_seconds
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "CNPJ-Email-Extractor/1.0 (+https://dadosbrasil.net)"}
        )

    def _get_json(self, path: str, params: dict | None = None) -> dict | list:
        url = f"{API_BASE}{path}"
        response = self.session.get(url, params=params, timeout=30)
        response.raise_for_status()
        time.sleep(self.delay_seconds)
        return response.json()

    def _establishment_to_record(
        self, establishment: dict, legal_name: str = ""
    ) -> CompanyEmail | None:
        email = normalize_email(establishment.get("email", ""))
        if not is_valid_email(email):
            return None

        cnpj = clean_cnpj(establishment.get("tax_id", ""))
        if not cnpj:
            cnpj = f"{establishment.get('cnpj', '')}{establishment.get('tax_id_order', '')}{establishment.get('tax_id_check_digit', '')}"
            cnpj = clean_cnpj(cnpj)

        state = establishment.get("state") or {}
        city = establishment.get("city") or {}
        primary = establishment.get("primary_activity") or {}

        return CompanyEmail(
            cnpj=cnpj,
            email=email,
            razao_social=legal_name,
            nome_fantasia=(establishment.get("trade_name") or "").strip(),
            telefone=format_phone(
                establishment.get("area_code_1", ""),
                establishment.get("phone_1", ""),
            ),
            uf=(state.get("code") or "").strip(),
            municipio=(city.get("name") or "").strip(),
            cnae=(primary.get("id") or establishment.get("primary_cnae") or "").strip(),
            situacao=normalize_situacao(
                str(establishment.get("registration_status", ""))
            ),
            fonte=self.name,
        )

    def fetch_company(self, cnpj: str) -> list[CompanyEmail]:
        base = clean_cnpj(cnpj)[:8]
        if len(base) != 8:
            return []

        data = self._get_json(f"/companies/{base}")
        legal_name = (data.get("legal_name") or "").strip()
        records: list[CompanyEmail] = []

        establishment = data.get("establishment")
        if establishment:
            record = self._establishment_to_record(establishment, legal_name)
            if record:
                records.append(record)

        establishments = self._get_json(f"/companies/{base}/establishments")
        if isinstance(establishments, list):
            for item in establishments:
                record = self._establishment_to_record(item, legal_name)
                if record and all(r.cnpj != record.cnpj or r.email != record.email for r in records):
                    records.append(record)
        return records

    def list_companies(
        self,
        *,
        uf: str | None = None,
        cnae: str | None = None,
        city_ibge: str | None = None,
        limit: int = 100,
        max_pages: int = 10,
    ) -> list[dict]:
        params: dict[str, str | int] = {"limit": min(limit, 100)}
        if uf:
            params["uf"] = uf.upper()
        if cnae:
            params["primary_cnae"] = clean_cnpj(cnae)[:7]
        if city_ibge:
            params["city_ibge"] = city_ibge

        items: list[dict] = []
        cursor: str | None = None
        pages = 0
        while pages < max_pages:
            page_params = dict(params)
            if cursor:
                page_params["cursor"] = cursor
            payload = self._get_json("/companies", page_params)
            batch = payload.get("items", [])
            items.extend(batch)
            if not payload.get("hasMore") or not payload.get("nextCursor"):
                break
            cursor = payload["nextCursor"]
            pages += 1
        return items

    def extract(
        self,
        *,
        cnpj_list: list[str] | None = None,
        uf: str | None = None,
        cnae: str | None = None,
        city_ibge: str | None = None,
        max_records: int | None = 500,
        fetch_all_establishments: bool = True,
        progress_callback: ProgressCallback = None,
    ) -> Iterator[CompanyEmail]:
        seen: set[tuple[str, str]] = set()
        found = 0

        if cnpj_list:
            total = len(cnpj_list)
            for index, cnpj in enumerate(cnpj_list):
                for record in self.fetch_company(cnpj):
                    key = (record.cnpj, record.email)
                    if key in seen:
                        continue
                    seen.add(key)
                    yield record
                    found += 1
                    if max_records and found >= max_records:
                        return
                self._report(
                    progress_callback,
                    (index + 1) / total,
                    f"CNPJ {index + 1}/{total} processado",
                )
            return

        companies = self.list_companies(
            uf=uf,
            cnae=cnae,
            city_ibge=city_ibge,
            limit=100,
            max_pages=max(1, (max_records or 500) // 100),
        )
        total = len(companies)
        for index, company in enumerate(companies):
            base = company.get("cnpj", "")
            if fetch_all_establishments:
                records = self.fetch_company(base)
            else:
                data = self._get_json(f"/companies/{base}")
                establishment = data.get("establishment")
                records = []
                if establishment:
                    record = self._establishment_to_record(
                        establishment, data.get("legal_name", "")
                    )
                    if record:
                        records.append(record)

            for record in records:
                key = (record.cnpj, record.email)
                if key in seen:
                    continue
                seen.add(key)
                yield record
                found += 1
                if max_records and found >= max_records:
                    return

            self._report(
                progress_callback,
                (index + 1) / max(total, 1),
                f"Empresa {index + 1}/{total} — {found} e-mails",
            )

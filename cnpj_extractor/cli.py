#!/usr/bin/env python3
"""CLI para extração de e-mails de empresas (Brasil e Portugal)."""

from __future__ import annotations

import argparse
from pathlib import Path

from cnpj_extractor.database import export_csv, export_sqlite
from cnpj_extractor.sources import COUNTRIES, SOURCES
from cnpj_extractor.sources.fiz_portugal import FIZ_SITEMAP_INDEX
from cnpj_extractor.utils import dedupe_records, format_cnpj, parse_cnpj_list


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extrai e-mails de empresas (Brasil e Portugal) via sitemap, API ou dados abertos."
    )
    parser.add_argument("--pais", choices=["BR", "PT"], default="BR", help="País (BR ou PT)")
    parser.add_argument(
        "--fonte",
        choices=list(SOURCES.keys()),
        default=None,
        help="Fonte de dados (default: receita_federal para BR, fiz_portugal para PT)",
    )
    parser.add_argument("--auto", action="store_true", help="Modo automático: sitemap/base completa")
    parser.add_argument("--uf", help="Filtrar por UF (Brasil)")
    parser.add_argument("--cnae", help="Filtrar por CNAE (Brasil)")
    parser.add_argument("--distrito", help="Filtrar por distrito/cidade (Portugal)")
    parser.add_argument("--cnpjs", help="Lista de CNPJs separados por vírgula")
    parser.add_argument("--cnpjs-file", help="Ficheiro com CNPJs")
    parser.add_argument("--sitemap", default=FIZ_SITEMAP_INDEX, help="URL do sitemap (Portugal/genérico)")
    parser.add_argument("--max", type=int, default=500, help="Limite de registros (0 = sem limite)")
    parser.add_argument("--output", "-o", required=True, help="Ficheiro de saída (.db ou .csv)")
    parser.add_argument("--release", help="Versão dos dados RFB")
    parser.add_argument("--partitions", help="Partições RFB (ex: 0,1,2,...,9)")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    country = COUNTRIES[args.pais]
    source_key = args.fonte or ("receita_federal" if args.pais == "BR" else "fiz_portugal")
    source = SOURCES[source_key]

    cnpj_list: list[str] = []
    if args.cnpjs:
        cnpj_list.extend(parse_cnpj_list(args.cnpjs))
    if args.cnpjs_file:
        cnpj_list.extend(parse_cnpj_list(Path(args.cnpjs_file).read_text(encoding="utf-8")))

    max_records = None if args.max == 0 else args.max
    kwargs: dict = {"max_records": max_records, "progress_callback": None}

    if source_key == "receita_federal":
        kwargs.update({
            "release": args.release,
            "partitions": (
                [int(p) for p in args.partitions.split(",")]
                if args.partitions
                else (list(range(10)) if args.auto else [0])
            ),
            "uf_filter": args.uf,
        })
    elif source_key == "dadosbrasil_api":
        kwargs.update({"cnpj_list": cnpj_list or None, "uf": args.uf, "cnae": args.cnae})
    elif source_key == "dadosbrasil_scraper":
        if not cnpj_list:
            raise SystemExit("dadosbrasil_scraper requer --cnpjs ou --cnpjs-file")
        kwargs["cnpj_list"] = cnpj_list
    elif source_key == "fiz_portugal":
        kwargs.update({
            "auto_discover": True,
            "distrito": args.distrito,
            "max_sitemap_pages": None if args.auto else 1,
        })
    elif source_key == "sitemap_generico":
        kwargs.update({
            "sitemap_url": args.sitemap,
            "auto_discover": args.auto,
        })

    records = []
    for record in source.extract(**kwargs):
        row = record.to_dict()
        if args.pais == "BR" and row.get("cnpj"):
            row["cnpj"] = format_cnpj(row["cnpj"])
        records.append(row)

    records = dedupe_records(records)
    output = Path(args.output)
    if output.suffix.lower() == ".csv":
        export_csv(records, output)
    else:
        export_sqlite(records, output)

    print(f"[{country['name']}] Exportados {len(records):,} registos para {output}")


if __name__ == "__main__":
    main()

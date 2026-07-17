#!/usr/bin/env python3
"""CLI para extração de e-mails de empresas."""

from __future__ import annotations

import argparse
from pathlib import Path

from cnpj_extractor.database import export_csv, export_sqlite
from cnpj_extractor.sources import SOURCES
from cnpj_extractor.utils import dedupe_records, format_cnpj, parse_cnpj_list


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extrai e-mails de empresas brasileiras a partir de dados públicos CNPJ."
    )
    parser.add_argument(
        "--fonte",
        choices=list(SOURCES.keys()),
        default="dadosbrasil_api",
        help="Fonte de dados (default: dadosbrasil_api)",
    )
    parser.add_argument("--uf", help="Filtrar por UF (ex: SP)")
    parser.add_argument("--cnae", help="Filtrar por CNAE")
    parser.add_argument("--cnpjs", help="Lista de CNPJs separados por vírgula")
    parser.add_argument("--cnpjs-file", help="Ficheiro com CNPJs (um por linha)")
    parser.add_argument("--max", type=int, default=500, help="Limite de registros")
    parser.add_argument("--output", "-o", required=True, help="Ficheiro de saída (.db ou .csv)")
    parser.add_argument("--release", help="Versão dos dados RFB (ex: 2026-01-11)")
    parser.add_argument(
        "--partitions",
        help="Partições RFB separadas por vírgula (ex: 0,1,2). Default: 0",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    source = SOURCES[args.fonte]

    cnpj_list: list[str] = []
    if args.cnpjs:
        cnpj_list.extend(parse_cnpj_list(args.cnpjs))
    if args.cnpjs_file:
        text = Path(args.cnpjs_file).read_text(encoding="utf-8")
        cnpj_list.extend(parse_cnpj_list(text))

    kwargs: dict = {"max_records": args.max}
    if args.fonte == "receita_federal":
        kwargs.update(
            {
                "release": args.release,
                "partitions": [int(p) for p in args.partitions.split(",")] if args.partitions else [0],
                "uf_filter": args.uf,
            }
        )
    elif args.fonte == "dadosbrasil_api":
        kwargs.update(
            {
                "cnpj_list": cnpj_list or None,
                "uf": args.uf,
                "cnae": args.cnae,
            }
        )
    elif args.fonte == "dadosbrasil_scraper":
        if not cnpj_list:
            raise SystemExit("dadosbrasil_scraper requer --cnpjs ou --cnpjs-file")
        kwargs["cnpj_list"] = cnpj_list

    records = []
    for record in source.extract(**kwargs):
        row = record.to_dict()
        row["cnpj"] = format_cnpj(row["cnpj"])
        records.append(row)

    records = dedupe_records(records)
    output = Path(args.output)
    if output.suffix.lower() == ".csv":
        export_csv(records, output)
    else:
        export_sqlite(records, output)

    print(f"Exportados {len(records)} registos para {output}")


if __name__ == "__main__":
    main()

# CNPJ Email Extractor

Software para extrair e-mails de empresas brasileiras a partir de **dados públicos oficiais** da Receita Federal, com interface web simples e exportação para SQLite ou CSV (compatível com DB Browser for SQLite).

## Fontes de dados

| Fonte | Tipo | Descrição |
|-------|------|-----------|
| **Receita Federal** | Download em massa | Base oficial (~67M empresas). Processa ficheiros `Estabelecimentos*.zip` |
| **DadosBrasil API** | API REST gratuita | Consultas por UF, CNAE ou lista de CNPJs via [api.dadosbrasil.net](https://api.dadosbrasil.net) |
| **DadosBrasil Scraper** | Web scraping | Extrai dados de páginas HTML do [dadosbrasil.net](https://dadosbrasil.net) |

> **Nota:** Plataformas comerciais como Oportunidados, Econodata e BaseCNPJ utilizam os mesmos dados públicos da Receita Federal, mas exigem subscrição paga e possuem proteção anti-bot. Este software usa as fontes oficiais gratuitas.

## Instalação

```bash
pip install -r requirements.txt
```

## Interface web

```bash
streamlit run app.py
```

Abre o browser em `http://localhost:8501`.

### Funcionalidades

- Filtros por UF, situação cadastral, limite de registros
- Consulta por lista de CNPJs
- Extração em massa da Receita Federal (com partições configuráveis)
- Pré-visualização dos resultados
- Exportação para **SQLite** (`.db`) ou **CSV**
- Esquema compatível com [DB Browser for SQLite](https://sqlitebrowser.org/)

## Linha de comandos (CLI)

```bash
# Consulta rápida por UF via API
python -m cnpj_extractor.cli --fonte dadosbrasil_api --uf SP --max 100 -o empresas_sp.db

# Exportar para CSV
python -m cnpj_extractor.cli --fonte dadosbrasil_api --uf RJ --max 200 -o empresas_rj.csv

# Lista de CNPJs específicos
python -m cnpj_extractor.cli --fonte dadosbrasil_api --cnpjs "33000167000101,00000000000191" -o resultado.db

# Receita Federal (amostra — 1 partição)
python -m cnpj_extractor.cli --fonte receita_federal --uf SP --max 1000 -o rfb_sp.db
```

## Esquema SQLite

```sql
CREATE TABLE empresas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cnpj TEXT NOT NULL,
    razao_social TEXT,
    nome_fantasia TEXT,
    email TEXT NOT NULL,
    telefone TEXT,
    uf TEXT,
    municipio TEXT,
    cnae TEXT,
    situacao TEXT,
    fonte TEXT,
    data_extracao TEXT
);
```

## Requisitos de sistema

- Python 3.10+
- Para extração completa da Receita Federal: ~15 GB de espaço em disco
- Ligação à internet para download dos dados

## Aviso legal

Os dados são públicos e fornecidos pela Receita Federal do Brasil (Lei 12.527/2011). Utilize de acordo com a LGPD e apenas para fins legítimos de prospecção B2B. Para decisões fiscais ou legais, consulte sempre a fonte oficial.

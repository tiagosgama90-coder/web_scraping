# Company Email Extractor

Software para extrair e-mails de empresas de **Brasil** e **Portugal**, com descoberta automática de sitemaps, interface web e exportação para SQLite ou CSV (compatível com DB Browser for SQLite).

## Países suportados

### 🇵🇹 Portugal — Diretório FIZ

| Fonte | Cobertura | Modo |
|-------|-----------|------|
| **Diretório FIZ** | ~490.000 empresas (98 páginas × 5.000) | Sitemap automático |
| **Sitemap Genérico** | Qualquer site com estrutura semelhante | URL configurável |

O software descobre automaticamente todas as páginas do sitemap (`/empresas/1` até `/empresas/98`) — **não precisa inserir 1, 2, 3... manualmente**.

### 🇧🇷 Brasil — Receita Federal

| Fonte | Cobertura | Modo |
|-------|-----------|------|
| **Receita Federal** | ~67 milhões de empresas | Download em massa (10 partições) |
| **DadosBrasil API** | Consultas filtradas | API REST gratuita |
| **DadosBrasil Scraper** | Por CNPJ | Web scraping |

## Instalação

```bash
pip install -r requirements.txt
```

## Interface web

```bash
streamlit run app.py
```

1. Escolha o **país** (Brasil ou Portugal)
2. Escolha a **fonte** de dados
3. Modo **Automático** = sitemap/base completa (descobre tudo sozinho)
4. Modo **Limitado** = teste rápido (primeira página do sitemap)
5. Exporte para **SQLite** ou **CSV**

## Linha de comandos (CLI)

### Portugal — teste rápido (5 e-mails)

```bash
python3 -m cnpj_extractor.cli --pais PT --fonte fiz_portugal --max 5 -o portugal_teste.db
```

### Portugal — extração completa (~490.000 empresas)

```bash
python3 -m cnpj_extractor.cli --pais PT --fonte fiz_portugal --auto --max 0 -o portugal_completo.db
```

### Portugal — outro site com sitemap

```bash
python3 -m cnpj_extractor.cli --pais PT --fonte sitemap_generico \
  --sitemap "https://diretorio.fiz.co/sitemap.xml" --auto --max 0 -o resultado.db
```

### Brasil — teste rápido

```bash
python3 -m cnpj_extractor.cli --pais BR --fonte dadosbrasil_api --uf SP --max 100 -o brasil_sp.db
```

### Brasil — extração nacional completa

```bash
python3 -m cnpj_extractor.cli --pais BR --fonte receita_federal --auto --max 0 -o brasil_completo.db
```

## Como funciona o sitemap automático

```
sitemap.xml  →  descobre /empresas/1 ... /empresas/98 automaticamente
     ↓
cada página tem 5.000 URLs de empresas
     ↓
cada URL é visitada e o e-mail extraído do JSON-LD (schema.org)
     ↓
exportação para SQLite ou CSV
```

**URL base Portugal:** `https://diretorio.fiz.co/api/sitemap/empresas/1`  
**Índice completo:** `https://diretorio.fiz.co/sitemap.xml`

Para outros sites, cole o `sitemap.xml` na fonte **Sitemap Genérico**.

## Esquema SQLite

```sql
CREATE TABLE empresas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cnpj TEXT NOT NULL,       -- CNPJ (BR) ou NIPC (PT)
    razao_social TEXT,
    nome_fantasia TEXT,
    email TEXT NOT NULL,
    telefone TEXT,
    uf TEXT,
    municipio TEXT,
    cnae TEXT,
    situacao TEXT,
    pais TEXT,                -- BR ou PT
    website TEXT,
    fonte TEXT,
    data_extracao TEXT
);
```

## Requisitos

- Python 3.10+
- Internet para download/scraping
- Extração completa BR: ~15 GB de espaço
- Extração completa PT: ~490K requests (várias horas)

## Aviso legal

Utilize os dados de acordo com a LGPD (Brasil) e RGPD (Portugal). Respeite os `robots.txt` dos sites. Para decisões legais ou fiscais, consulte sempre as fontes oficiais.

# Company Email Extractor

Software para extrair e-mails de empresas de **Brasil** e **Portugal** — interface gráfica, sem configuração técnica.

---

## Windows — usar em 2 passos (sem instalar Python)

### 1. Descarregar
https://github.com/tiagosgama90-coder/web_scraping → **Code** → **Download ZIP**

### 2. Instalar e abrir

| Ficheiro | Quando usar |
|----------|-------------|
| **`INSTALAR.bat`** | Duplo clique **uma vez** (instala tudo automaticamente) |
| **`ABRIR SOFTWARE.bat`** | Duplo clique **sempre que quiseres usar** o software |

O instalador:
- Descarrega Python portátil (não mexe no Windows)
- Instala todas as dependências sozinho
- Cria atalho no Ambiente de Trabalho

📖 **Guia completo:** [COMO_USAR.md](COMO_USAR.md)

---

## Executável (.exe) — zero instalação

Descarrega `CompanyEmailExtractor-Windows.zip` nos **Artifacts** do GitHub Actions (aba Actions do repositório) ou corre `build_windows.bat` no Windows para gerar localmente.

Duplo clique em `CompanyEmailExtractor.exe` → o browser abre sozinho.

---

## Países suportados

### 🇵🇹 Portugal — Diretório FIZ (~490.000 empresas)
Sitemap automático — descobre as 98 páginas sozinho.

### 🇧🇷 Brasil — Receita Federal (~67 milhões de empresas)
Dados abertos oficiais + API DadosBrasil.

---

## Interface web (desenvolvimento / Mac / Linux)

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## Linha de comandos (opcional)

```bash
# Portugal - teste
python -m cnpj_extractor.cli --pais PT --fonte fiz_portugal --max 10 -o teste.db

# Portugal - completo
python -m cnpj_extractor.cli --pais PT --fonte fiz_portugal --auto --max 0 -o portugal.db

# Brasil - teste
python -m cnpj_extractor.cli --pais BR --fonte dadosbrasil_api --uf SP --max 100 -o teste.db

# Brasil - completo
python -m cnpj_extractor.cli --pais BR --fonte receita_federal --auto --max 0 -o brasil.db
```

---

## Requisitos

| Modo | Requisitos |
|------|------------|
| **INSTALAR.bat** (Windows) | Só internet na 1ª vez |
| **Executável .exe** | Nenhum — tudo incluído |
| **Desenvolvimento** | Python 3.10+ |

---

## Aviso legal

Utilize os dados em conformidade com a LGPD (Brasil) e RGPD (Portugal).

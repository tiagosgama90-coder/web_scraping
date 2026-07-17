# Company Email Extractor v2.0

Software **nativo Windows** para extrair e-mails de empresas do **Brasil** e **Portugal**.

**Janela própria — sem browser, sem terminal, sem configurar Python.**

---

## Instalação rápida (Windows)

### Opção 1 — Instalador automático (recomendado)

1. Descarrega o ZIP: https://github.com/tiagosgama90-coder/web_scraping
2. Duplo clique em **`INSTALAR.bat`** (uma vez)
3. Duplo clique em **`ABRIR SOFTWARE.bat`** (sempre)

### Opção 2 — Setup profissional (.exe instalador)

1. GitHub → **Actions** → **Build Windows Native App**
2. Descarrega **`CompanyEmailExtractor-Installer`**
3. Corre **`CompanyEmailExtractor-Setup.exe`**
4. Segue o assistente de instalação
5. Abre pelo menu Iniciar ou atalho no Ambiente de Trabalho

### Opção 3 — Executável portátil (sem instalar)

Descarrega `CompanyEmailExtractor.exe` nos Artifacts do GitHub. Duplo clique — funciona.

---

## Interface

```
┌─────────────────────────────────────────────────────┐
│  📧 Company Email Extractor                         │
├──────────────┬──────────────────────────────────────┤
│ País         │  [Registos] [E-mails] [País] [Estado]│
│ Fonte        │  ████████████░░░░░░  Progresso       │
│ Modo         │  ┌────────────────────────────────┐  │
│ Limite       │  │ NIPC │ Empresa │ Email │ ...  │  │
│ Filtros      │  └────────────────────────────────┘  │
│              │  [Exportar SQLite] [Exportar CSV]     │
│ [▶ Iniciar]  │                                      │
└──────────────┴──────────────────────────────────────┘
```

---

## Países

| País | Fonte | Empresas |
|------|-------|----------|
| 🇵🇹 Portugal | Diretório FIZ | ~490.000 (sitemap automático) |
| 🇧🇷 Brasil | Receita Federal / DadosBrasil | ~67 milhões |

---

## Modos

| Modo | Descrição |
|------|-----------|
| **Limitado** | Teste rápido (primeira página / amostra) |
| **Automático** | Extração completa (todas as páginas do sitemap) |

---

## Documentação

📖 Guia completo: [COMO_USAR.md](COMO_USAR.md)

## Build (desenvolvedores)

```bash
build_windows.bat
# ou
pip install -r requirements.txt -r requirements-build.txt
pyinstaller company_email_extractor.spec --noconfirm
```

Instalador Setup: abrir `installer/setup.iss` no Inno Setup 6.

---

## Aviso legal

Utilize em conformidade com LGPD (Brasil) e RGPD (Portugal).

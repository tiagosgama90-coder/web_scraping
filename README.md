# Company Email Extractor v2.6

Software **nativo Windows** para extrair emails e dados de empresas do **Brasil**, **Portugal** e **qualquer site**.

**Janela própria — sem browser, sem terminal, sem configurar Python.**

---

## Download Windows (Setup)

**https://github.com/tiagosgama90-coder/web_scraping/releases/latest**

Ficheiro: `CompanyEmailExtractor-Setup.exe` (~83 MB)

O instalador inclui o programa + guias **LEIA-ME.txt** e **COMO_USAR.md**.

---

## O que faz (resumo)

- Extrai emails de Receita Federal (BR), FIZ (PT) e sites personalizados
- Limpa emails inválidos, duplicados e lixo automaticamente
- Grava **CSV**, **TXT** e **SQLite** enquanto extrai (v2.6)
- Divide em ficheiros de **1000 linhas** (abre no Excel)
- Brasil: extrai **UF por UF** (SP, RJ, MG…) em pastas separadas
- Anti-bot integrado (Cloudflare, Playwright)

---

## Documentação

| Ficheiro | Conteúdo |
|----------|----------|
| **[COMO_USAR.md](COMO_USAR.md)** | Guia completo v2.6 |
| **[LEIA-ME.txt](LEIA-ME.txt)** | Resumo rápido (vai no instalador) |

---

## Instalação rápida

1. Descarrega `CompanyEmailExtractor-Setup.exe`
2. Instala → abre pelo Menu Iniciar
3. Lê `LEIA-ME.txt` na pasta de instalação

Alternativa (código fonte): `INSTALAR.bat` → `ABRIR SOFTWARE.bat`

---

## Build (desenvolvedores)

```bash
build_windows.bat
installer\build_setup.bat   # Gera Setup.exe + inclui guias
```

---

## Licença e aviso legal

Use os dados em conformidade com **LGPD** (Brasil) e **RGPD** (Portugal).

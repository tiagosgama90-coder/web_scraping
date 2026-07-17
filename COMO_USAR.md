# Como usar o Company Email Extractor (Windows)

Guia simples — **sem precisar de saber programar**.

---

## Opção A — Mais fácil (recomendada): duplo clique

### 1. Descarregar o projeto

Vai a: **https://github.com/tiagosgama90-coder/web_scraping**

Clica **Code** → **Download ZIP** → descompacta a pasta.

### 2. Instalar (só uma vez)

Dentro da pasta, faz **duplo clique** em:

```
INSTALAR.bat
```

O instalador faz tudo sozinho:
- Descarrega Python portátil (não mexe no teu sistema)
- Instala todas as dependências
- Cria atalho no Ambiente de Trabalho

Demora **2–5 minutos** na primeira vez.

### 3. Abrir o software (sempre que quiseres)

Faz duplo clique em:

```
ABRIR SOFTWARE.bat
```

Ou usa o atalho **Company Email Extractor** no Ambiente de Trabalho.

O browser abre automaticamente em: **http://localhost:8501**

### 4. Usar o software

| Passo | O que fazer |
|-------|-------------|
| 1 | Escolhe o **país** (🇧🇷 Brasil ou 🇵🇹 Portugal) |
| 2 | Escolhe a **fonte** de dados |
| 3 | Modo **Limitado** = teste rápido / **Automático** = extração completa |
| 4 | Clica **▶️ Iniciar extração** |
| 5 | Vê resultados em **📊 Resultados** |
| 6 | Exporta em **💾 Exportar** → SQLite ou CSV |

### 5. Fechar

Fecha a janela preta (terminal) ou prime **Ctrl+C**.

---

## Opção B — Executável (.exe) sem instalar nada

Se existir build disponível nos **Releases** ou **Actions** do GitHub:

1. Descarrega `CompanyEmailExtractor-Windows.zip`
2. Descompacta
3. Duplo clique em `CompanyEmailExtractor.exe`
4. O browser abre sozinho

> Nota: o .exe tem ~200–400 MB porque inclui Python e todas as bibliotecas.

---

## Exemplos rápidos

### 🇵🇹 Portugal — teste (2 minutos)

1. País: **Portugal**
2. Fonte: **Diretório FIZ**
3. Modo: **Limitado**
4. Limite: **50**
5. **Iniciar extração**

### 🇵🇹 Portugal — completo (~8–15 horas)

1. País: **Portugal**
2. Fonte: **Diretório FIZ**
3. Modo: **Automático**
4. Limite: **0** (sem limite)
5. **Iniciar extração** e deixa correr

### 🇧🇷 Brasil — teste (2 minutos)

1. País: **Brasil**
2. Fonte: **DadosBrasil API**
3. UF: **SP**
4. Modo: **Limitado**, limite **100**
5. **Iniciar extração**

### 🇧🇷 Brasil — completo (~6–24 horas)

1. País: **Brasil**
2. Fonte: **Receita Federal**
3. Modo: **Automático**
4. Limite: **0**
5. **Iniciar extração**

---

## Abrir resultados

### SQLite (.db)
1. Instala [DB Browser for SQLite](https://sqlitebrowser.org/)
2. **Open Database** → escolhe o ficheiro `.db`
3. Tabela: **empresas**

### CSV
Abre diretamente no **Excel** ou Google Sheets.

---

## Estrutura de ficheiros

```
web_scraping/
├── INSTALAR.bat          ← 1º passo: instalar (só uma vez)
├── ABRIR SOFTWARE.bat    ← Abrir o software
├── install.ps1           ← Script de instalação (automático)
├── app.py                ← Interface web
├── runtime/              ← Python portátil (criado pelo instalador)
└── cnpj_extractor/       ← Motor de extração
```

---

## Problemas comuns

| Problema | Solução |
|----------|---------|
| "Python não encontrado" ao usar INSTALAR.bat | Clica com botão direito → Executar como administrador |
| Browser não abre | Abre manualmente: http://localhost:8501 |
| Porta 8501 ocupada | Fecha outras janelas do software e tenta de novo |
| Instalação falha | Verifica ligação à internet e volta a correr INSTALAR.bat |
| Antivírus bloqueia | Adiciona a pasta à lista de exceções |

---

## Para programadores (opcional)

```bash
# Build do .exe no Windows
build_windows.bat

# Ou manualmente
pip install -r requirements.txt -r requirements-build.txt
pyinstaller company_email_extractor.spec --noconfirm
```

O executável fica em: `dist\CompanyEmailExtractor\CompanyEmailExtractor.exe`

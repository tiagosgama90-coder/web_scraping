# Como usar — Company Email Extractor v2.0

**Software nativo Windows** — janela própria, sem browser, sem terminal.

---

## Instalação

### Método 1 — Duplo clique (mais fácil)

1. Descarrega o ZIP do GitHub
2. **`INSTALAR.bat`** → duplo clique (só uma vez, 2–5 min)
3. **`ABRIR SOFTWARE.bat`** → duplo clique (sempre que quiseres usar)

Aparece uma **janela do programa** — não abre o browser.

### Método 2 — Instalador Setup (.exe)

1. GitHub → separador **Actions**
2. Workflow **Build Windows Native App**
3. Descarrega artifact **`CompanyEmailExtractor-Installer`**
4. Corre **`CompanyEmailExtractor-Setup.exe`**
5. Segue o assistente (Next → Install → Finish)
6. Abre pelo **Menu Iniciar** ou atalho no Ambiente de Trabalho

### Método 3 — Executável portátil

Descarrega `CompanyEmailExtractor.exe` → duplo clique → funciona sem instalar.

---

## Usar o software

### Passo 1 — Configurar (barra lateral esquerda)

| Campo | O que escolher |
|-------|----------------|
| **País** | Portugal ou Brasil |
| **Fonte** | FIZ (PT) ou Receita Federal / DadosBrasil (BR) |
| **Modo** | `limitado` = teste / `automatico` = completo |
| **Limite** | `100` para teste / `0` para tudo |
| **Filtros** | UF (Brasil) ou distrito (Portugal) |

### Passo 2 — Extrair

Clica **▶ Iniciar Extração**

- Barra de progresso mostra o estado
- Tabela mostra os resultados em tempo real
- **⏹ Parar** interrompe a extração

### Passo 3 — Exportar

| Botão | Resultado |
|-------|-----------|
| **💾 Exportar SQLite** | Ficheiro `.db` para DB Browser |
| **📄 Exportar CSV** | Ficheiro `.csv` para Excel |

---

## Exemplos

### 🇵🇹 Portugal — teste (2 min)
- País: **PT**
- Fonte: **Diretório FIZ**
- Modo: **limitado**
- Limite: **50**

### 🇵🇹 Portugal — completo (8–15 h)
- País: **PT**
- Modo: **automatico**
- Limite: **0**

### 🇧🇷 Brasil — teste (2 min)
- País: **BR**
- Fonte: **DadosBrasil API**
- UF: **SP**
- Limite: **100**

### 🇧🇷 Brasil — completo (6–24 h)
- País: **BR**
- Fonte: **Receita Federal**
- Modo: **automatico**
- Limite: **0**

---

## Diferença entre as opções de instalação

| | INSTALAR.bat | Setup.exe | .exe portátil |
|---|---|---|---|
| **Aspecto** | Pasta com ficheiros | Instalador profissional | Um ficheiro só |
| **Menu Iniciar** | Atalho manual | Sim | Não |
| **Desinstalar** | Apagar pasta | Painel de Controlo | Apagar ficheiro |
| **Tamanho** | ~150 MB | ~80 MB | ~80 MB |
| **Melhor para** | Desenvolvimento | Utilizador final | USB / teste rápido |

---

## Problemas comuns

| Problema | Solução |
|----------|---------|
| Janela não abre | Corre `INSTALAR.bat` primeiro |
| Antivírus bloqueia | Adiciona exceção para a pasta |
| Extração lenta | Normal no modo automático |
| 0 resultados | Testa com limite 10, modo limitado |

---

## Abrir resultados

- **SQLite (.db):** [DB Browser for SQLite](https://sqlitebrowser.org/) → tabela `empresas`
- **CSV:** Abre no Excel

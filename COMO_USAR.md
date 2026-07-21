# Company Email Extractor v2.6 — Guia Completo

**Software nativo Windows** para extrair emails e dados de empresas do Brasil, Portugal e qualquer site.

- Janela própria — **sem browser**, sem terminal, sem instalar Python
- Grava ficheiros **enquanto extrai** — ideal para milhões de registos
- Versão atual: **2.6.0**

---

## Índice

1. [O que o programa faz](#1-o-que-o-programa-faz)
2. [Instalação Windows](#2-instalação-windows)
3. [Interface e opções](#3-interface-e-opções)
4. [Formatos de exportação](#4-formatos-de-exportação)
5. [Como usar — passo a passo](#5-como-usar--passo-a-passo)
6. [Brasil — milhões de emails](#6-brasil--milhões-de-emails)
7. [Portugal](#7-portugal)
8. [Sites e bases personalizadas](#8-sites-e-bases-personalizadas)
9. [Onde ficam os ficheiros](#9-onde-ficam-os-ficheiros)
10. [Riscos e como evitar problemas](#10-riscos-e-como-evitar-problemas)
11. [Problemas comuns](#11-problemas-comuns)
12. [Avisos legais](#12-avisos-legais)

---

## 1. O que o programa faz

### Extração de dados

| País | Fonte | Volume aproximado |
|------|-------|-------------------|
| 🇧🇷 Brasil | Receita Federal (ZIPs oficiais) | ~67 milhões de empresas |
| 🇧🇷 Brasil | DadosBrasil API | Consultas por UF |
| 🇵🇹 Portugal | Diretório FIZ | ~490.000 empresas |
| 🌍 Qualquer | Site personalizado (URL/sitemap) | Conforme o site |

### Limpeza automática de emails

O programa **limpa sempre** os emails extraídos:

- Remove formatos inválidos (sem `@`, domínio errado, etc.)
- Remove lixo: `noreply@`, `no-reply@`, `postmaster@`, etc.
- Remove domínios falsos: `example.com`, `test.com`, `sememail`, etc.
- Remove duplicados (fica 1 registo por email)
- Normaliza para minúsculas

### Validação extra (opcional)

- **Validar domínio DNS/MX** — verifica se o domínio tem servidor de correio
- **Não** verifica se a caixa de correio existe (bounce) — isso requer serviços pagos

### Filtros

- Obrigatório ter **email**, **telefone** ou **CNPJ/NIPC**
- Brasil: filtro por **UF**, apenas empresas **ativas**
- Portugal: filtro por **distrito**
- Escolha de **campos a exportar** (email, empresa, cnpj, telefone, uf, municipio, etc.)

### Gravação em tempo real (v2.6)

- Grava **CSV**, **TXT** e **SQLite** enquanto extrai — não espera pelo fim
- Divide em ficheiros de **1000 linhas** (configurável) — cada um abre no Excel
- **Extrair UF por UF** (Brasil) — pasta separada por estado (SP, RJ, MG…)
- Usa pouca RAM — só mostra os últimos 500 registos na tabela

### Anti-bot

- Contorna proteções Cloudflare e anti-bot (curl_cffi, cloudscraper, Playwright)
- Ativo por defeito para sites portugueses e fontes personalizadas

---

## 2. Instalação Windows

### Método recomendado — Setup.exe

1. Descarrega: **CompanyEmailExtractor-Setup.exe**
   - https://github.com/tiagosgama90-coder/web_scraping/releases/latest
2. Duplo clique no instalador
3. Segue o assistente: **Seguinte → Instalar → Concluir**
4. Abre pelo **Menu Iniciar** ou atalho no Ambiente de Trabalho

O instalador coloca na pasta de instalação:

```
C:\Users\TeuNome\AppData\Local\Programs\Company Email Extractor\
  CompanyEmailExtractor.exe    ← Programa
  COMO_USAR.md                 ← Este guia
  LEIA-ME.txt                  ← Resumo rápido
```

### Método alternativo — INSTALAR.bat

Para quem descarrega o código fonte do GitHub:

1. Duplo clique em **`INSTALAR.bat`** (uma vez, 2–5 min)
2. Duplo clique em **`ABRIR SOFTWARE.bat`** (sempre que quiser usar)

Instala Python portátil na pasta do projeto — não mexe no sistema.

### Requisitos

| Requisito | Detalhe |
|-----------|---------|
| Sistema | Windows 10 ou 11 (64 bits) |
| RAM | 4 GB mínimo (8 GB recomendado para volumes grandes) |
| Disco | 5–20 GB livres para extrações grandes (Brasil) |
| Internet | Necessária para download de ZIPs e sites |
| SQLite | **Não precisa instalar** — o programa cria ficheiros `.db` sozinho |

---

## 3. Interface e opções

### Barra lateral (configuração)

| Opção | Descrição | Recomendação |
|-------|-----------|--------------|
| **País** | PT, BR ou OUTRO | Conforme a fonte |
| **Fonte de dados** | FIZ, Receita Federal, personalizada… | Ver secção 5 |
| **Modo** | `limitado` = teste / `automatico` = completo | Teste com limitado |
| **Limite** | `50` = teste / `0` = sem limite | Começar com 50 |
| **Campos a exportar** | Marcar colunas desejadas | email, empresa, cnpj… |
| **Obrigatório ter e-mail** | Só exporta com email válido | ✅ Ativo |
| **Obrigatório ter telefone** | Só com telefone | Opcional |
| **Obrigatório ter CNPJ/NIPC** | Só com identificação fiscal | Opcional |
| **Validar domínio DNS/MX** | Verifica servidor de correio | Só em testes (lento) |
| **Guardar CSV filtrado ao concluir** | Exportação no fim (modo antigo) | Desligado se streaming ativo |
| **Dividir exportação** | Ficheiros de N linhas | ✅ 1000 linhas |
| **Gravar ficheiros enquanto extrai** | CSV/TXT em tempo real | ✅ Sempre ativo |
| **SQLite em tempo real** | Base de dados durante extração | ✅ Para volumes grandes |
| **Anti-Bot** | Playwright + Cloudflare | ✅ Ativo |
| **Pasta de downloads** | ZIPs Receita Federal (BR) | Configurável |
| **Pasta de exportação** | Onde guarda resultados | Configurável |

### Filtros Brasil (quando País = BR)

| Opção | Descrição |
|-------|-----------|
| **UF** | Estado (SP, RJ…) ou **Todos** |
| **Extrair UF por UF** | Processa SP, depois RJ, depois MG… (pastas separadas) |
| **Apenas ativas** | Ignora empresas baixadas/suspensas |
| **Carregar razão social** | Nome completo (requer ZIPs Empresas*.zip) |
| **Usar ZIPs já descarregados** | Usa ficheiros na pasta de downloads |
| **Limpar ZIPs corrompidos** | Apaga ZIPs inválidos para re-download |

### Botões de exportação (separador Extrair)

| Botão | Função |
|-------|--------|
| **📥 CSV filtrado** | CSV com colunas escolhidas |
| **📂 Guardar na pasta** | Exportação direta sem diálogo |
| **📝 Emails .txt** | 1 email por linha, ficheiro leve |
| **💾 SQLite (.db)** | Base de dados completa |
| **📄 CSV completo** | Todas as colunas |
| **📧 Só emails** | email, empresa, cnpj, uf, municipio |
| **📨 Marketing** | email + nome (Mailchimp, Brevo) |
| **🗑 Limpar** | Limpa resultados da tabela |

> Com **"Gravar ficheiros enquanto extrai"** ativo, os ficheiros são criados automaticamente — não precisa clicar nos botões no fim.

### Separadores

| Separador | Conteúdo |
|-----------|------------|
| **📊 Extrair** | Tabela, progresso, exportação |
| **➕ Minhas Fontes** | Adicionar sites/bases personalizadas |
| **📖 Guia** | Ajuda integrada + teste rápido |

---

## 4. Formatos de exportação

### Durante a extração (automático)

Cada pasta (ex: `UF_SP/`) contém:

| Ficheiro | Formato | Conteúdo |
|----------|---------|----------|
| `parte_0001.csv` | CSV | 1000 linhas, colunas escolhidas |
| `parte_0002.csv` | CSV | Próximas 1000 linhas |
| `emails_0001.txt` | TXT | 1 email por linha |
| `empresas.db` | SQLite | Base de dados completa |

### Formatos suportados

| Formato | Extensão | Abre com | Notas |
|---------|----------|----------|-------|
| CSV filtrado | `.csv` | Excel, LibreOffice | UTF-8 com BOM (acentos OK) |
| CSV só emails | `.csv` | Excel | 5 colunas |
| CSV marketing | `.csv` | Mailchimp, Brevo | email + nome |
| Emails texto | `.txt` | Notepad, qualquer editor | Mais leve que CSV |
| SQLite | `.db` | DB Browser for SQLite | Milhões de linhas |

### Formatos NÃO suportados

- Excel nativo (`.xlsx`) — use CSV (abre no Excel)
- JSON, XML, PDF

### Como abrir ficheiros SQLite

O programa **cria** ficheiros `.db` mas **não os abre**.

1. Descarrega **[DB Browser for SQLite](https://sqlitebrowser.org/)** (grátis)
2. Abre o ficheiro `empresas.db`
3. Vai à tabela **`empresas`**
4. Podes exportar para CSV a partir daí

---

## 5. Como usar — passo a passo

### Teste rápido (2 minutos) 🇵🇹

1. Abre o programa
2. País: **PT**
3. Fonte: **★ Diretório FIZ**
4. Modo: **limitado**, Limite: **50**
5. Clica **▶ Iniciar Extração**
6. Vê os ficheiros em `Documentos\CompanyEmailExtractor\export\`

### Brasil — um estado 🇧🇷

1. País: **BR**
2. Fonte: **★ Receita Federal**
3. UF: **SP** (só São Paulo)
4. Modo: **limitado**, Limite: **100**
5. **▶ Iniciar**

### Site qualquer 🌍

1. Separador **➕ Minhas Fontes**
2. Cola o URL (sitemap ou página)
3. Clica **Adicionar e usar**
4. **▶ Iniciar Extração**

---

## 6. Brasil — milhões de emails

### Configuração recomendada

| Opção | Valor |
|-------|-------|
| País | BR |
| Fonte | Receita Federal |
| UF | Todos |
| Extrair UF por UF | ✅ |
| Modo | automatico |
| Limite | 0 |
| Gravar enquanto extrai | ✅ |
| SQLite em tempo real | ✅ |
| Dividir exportação | 1000 linhas |
| Validar DNS/MX | ❌ (muito lento em milhões) |

### O que acontece (UF por UF)

Em vez de processar o Brasil inteiro de uma vez:

```
1. UF AC → extrai → guarda em UF_AC/
2. UF AL → extrai → guarda em UF_AL/
3. UF SP → extrai → guarda em UF_SP/
   ...
27. UF TO → extrai → guarda em UF_TO/
```

### ZIPs da Receita Federal

Coloca na pasta de downloads:

```
Estabelecimentos0.zip
Estabelecimentos1.zip
...
Estabelecimentos9.zip
```

Opcional (para nome da empresa):

```
Empresas0.zip … Empresas9.zip
```

- Marca **Usar ZIPs já descarregados** se os tens na pasta
- Se der erro "não é um zip" → clica **🗑 Limpar ZIPs corrompidos**

### Estimativas

| Volume | Ficheiros CSV (1000 linhas) | Espaço em disco |
|--------|-------------------------------|-----------------|
| 100.000 emails | ~100 ficheiros | ~50 MB |
| 1.000.000 emails | ~1.000 ficheiros | ~500 MB |
| 10.000.000 emails | ~10.000 ficheiros | ~5 GB |

---

## 7. Portugal

| Configuração | Teste | Completo |
|--------------|-------|----------|
| Fonte | Diretório FIZ | Diretório FIZ |
| Modo | limitado | automatico |
| Limite | 50 | 0 |
| Anti-Bot | ✅ | ✅ |
| Tempo estimado | 2 min | 8–15 horas |

Filtro opcional: **distrito** (ex: Lisboa)

---

## 8. Sites e bases personalizadas

### Adição rápida

1. Separador **➕ Minhas Fontes**
2. Cola URL → **Adicionar e usar**

### Adição completa

1. **➕ Adicionar Fonte**
2. Escolhe o tipo:

| Tipo | Quando usar | Exemplo |
|------|-------------|---------|
| **Sitemap XML** | Site com sitemap | `https://site.com/sitemap.xml` |
| **Lista de URLs** | Links diretos | Um URL por linha ou ficheiro .txt |
| **Página/Site** | Uma página ou site inteiro | `https://site.com/empresas` |

As fontes ficam guardadas permanentemente em:

```
C:\Users\TeuNome\AppData\Local\CompanyEmailExtractor\custom_sources.json
```

---

## 9. Onde ficam os ficheiros

### Pastas de trabalho

```
C:\Users\TeuNome\Documents\CompanyEmailExtractor\
  downloads\          ← ZIPs Receita Federal (Brasil)
  export\             ← Resultados da extração
```

### Estrutura de exportação (Brasil, todos os estados)

```
export\empresas_br_20250721_143000\
  UF_SP\
    parte_0001.csv
    parte_0002.csv
    emails_0001.txt
    empresas.db
  UF_RJ\
    parte_0001.csv
    empresas.db
  UF_MG\
    ...
```

### Pasta de instalação

```
C:\Users\TeuNome\AppData\Local\Programs\Company Email Extractor\
  CompanyEmailExtractor.exe
  COMO_USAR.md
  LEIA-ME.txt
```

---

## 10. Riscos e como evitar problemas

### Seguro (configuração por defeito v2.6)

| Situação | Risco |
|----------|-------|
| Gravar enquanto extrai | ✅ Baixo |
| SQLite em tempo real | ✅ Baixo |
| UF por UF | ✅ Baixo |
| Ficheiros de 1000 linhas | ✅ Baixo |

### Atenção

| Situação | Risco | Solução |
|----------|-------|---------|
| Desligar "Gravar enquanto extrai" com milhões | Alto — trava RAM | Manter ligado |
| DNS/MX com 10M emails | Muito lento (dias) | Só em testes pequenos |
| Abrir CSV gigante no Excel | Excel não abre | Usar ficheiros de 1000 linhas |
| Disco cheio | Falha ao gravar | Libertar 10–20 GB |
| ZIPs corrompidos | Erro na extração | Limpar ZIPs corrompidos |

---

## 11. Problemas comuns

| Problema | Solução |
|----------|---------|
| Janela não abre | Reinstalar com Setup.exe |
| Antivírus bloqueia | Adicionar exceção para a pasta |
| 0 resultados | Testar com limite 50, modo limitado |
| "File is not a zip file" | Limpar ZIPs corrompidos + re-download |
| Extração muito lenta | Normal no modo automático completo |
| Excel não abre o ficheiro | Usar `parte_0001.csv` (1000 linhas), não ficheiro único |
| Como abrir .db | Instalar DB Browser for SQLite |
| Site bloqueado | Ativar Anti-Bot; alguns sites não permitem scraping |

---

## 12. Avisos legais

- Use os dados em conformidade com **LGPD** (Brasil) e **RGPD** (Portugal)
- Não envie emails em massa sem **consentimento** do destinatário
- Respeite os **termos de uso** dos sites e bases de dados
- A validação DNS/MX **não garante** que o email existe — apenas que o domínio tem servidor de correio
- O programa **extrai e exporta dados** — não envia emails

---

## Ligações úteis

| Recurso | URL |
|---------|-----|
| Download Setup (última versão) | https://github.com/tiagosgama90-coder/web_scraping/releases/latest |
| Código fonte | https://github.com/tiagosgama90-coder/web_scraping |
| DB Browser (abrir .db) | https://sqlitebrowser.org/ |

---

*Company Email Extractor v2.6.0 — Guia do utilizador*

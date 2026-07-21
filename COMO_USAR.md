# Company Email Extractor v2.15 — Guia Completo

**Software nativo Windows** para extrair emails e dados de empresas de **19 países** e qualquer site.

- Versão atual: **2.15.0**
- Download: https://github.com/tiagosgama90-coder/web_scraping/releases/latest
- Ficheiro: `CompanyEmailExtractor-Setup.exe`

---

## Índice

1. [Tudo o que o programa faz (ponto a ponto)](#1-tudo-o-que-o-programa-faz-ponto-a-ponto)
2. [O que é VPN/Proxy e é gratuita?](#2-o-que-é-vpnproxy-e-é-gratuita)
3. [Instalação Windows](#3-instalação-windows)
4. [Interface — cada opção explicada](#4-interface--cada-opção-explicada)
5. [Como usar — passo a passo](#5-como-usar--passo-a-passo)
6. [Países e fontes disponíveis](#6-países-e-fontes-disponíveis)
7. [Formatos de exportação](#7-formatos-de-exportação)
8. [Onde ficam os ficheiros](#8-onde-ficam-os-ficheiros)
9. [Problemas comuns](#9-problemas-comuns)
10. [Avisos legais](#10-avisos-legais)

---

## 1. Tudo o que o programa faz (ponto a ponto)

### A) Extração de dados empresariais

1. **Lê emails e dados** de empresas a partir de bases oficiais, diretórios ou sites
2. **Brasil — Receita Federal**: processa ZIPs oficiais (~67 milhões de empresas)
3. **Brasil — DadosBrasil API**: consultas rápidas por UF/CNPJ
4. **Portugal — FIZ**: diretório com ~490.000 empresas via sitemap
5. **16 países com diretórios**: Espanha, França, Alemanha, Itália, UK, México, Argentina, Colômbia, Chile, Peru, EUA, Canadá, Holanda, Bélgica, Polónia, Roménia
6. **Sites personalizados**: qualquer URL, sitemap XML ou lista de links
7. **Separador «Diretórios»**: lista todas as fontes por país com botão **Usar**

### B) Limpeza automática de emails

8. Remove emails **inválidos** (sem `@`, domínio errado)
9. Remove **lixo**: `noreply@`, `no-reply@`, `postmaster@`
10. Remove domínios **falsos**: `example.com`, `test.com`
11. Remove **duplicados** (fica 1 registo por email)
12. Normaliza para **minúsculas**

### C) Filtros

13. **Obrigatório ter email** — só exporta com email válido
14. **Obrigatório ter telefone** — opcional
15. **Obrigatório ter CNPJ/NIPC** — opcional
16. **Filtro por setor** — CNAE (BR), CAE/ISIC (PT), NACE (EU), NAICS (US)
17. **Brasil**: filtro por UF, empresas ativas, UF por UF (SP, RJ, MG…)
18. **Portugal**: filtro por distrito
19. **Países com diretórios**: filtro por região/província/estado
20. **Escolha de campos** a exportar (email, empresa, cnpj, telefone, uf, etc.)

### D) Pré-visualização (ver antes de gravar)

21. Botão **🔍 Pré-visualizar** — captura amostra (ex: 25 registos)
22. Mostra emails na **tabela** do separador Extrair
23. **Não grava** CSV/SQLite durante a pré-visualização
24. Depois de validar → **▶ Iniciar Extração** para gravação completa

### E) Gravação em tempo real

25. Grava **CSV**, **TXT** e **SQLite** enquanto extrai (não espera pelo fim)
26. Divide em ficheiros de **1000 linhas** (abre no Excel)
27. **Brasil UF por UF**: pasta separada por estado (UF_SP, UF_RJ…)
28. Usa pouca RAM — mostra últimos 500 registos na tabela

### F) Anti-bot

29. Contorna proteções **Cloudflare** e anti-bot
30. Usa curl_cffi, cloudscraper e **Playwright** (browser real)
31. Ativo por defeito — pode desligar na barra lateral

### G) Hide My IP + Painel HUD (rádio digital)

32. **Painel HUD** no separador **Extrair** — fundo escuro, letras azuis estilo rádio de carro
33. Mostra **antes de extrair**: IP real, IP oculto, país, Hide My IP ON/OFF, browser/idioma
34. Estado do sistema: `CALIBRANDO` → `SCANNING` → `READY`
35. **Ocultar IP** ligado por defeito — integrado, sem VPN externa
36. **Randomizar impressão digital** — User-Agent, idioma, resolução (browser)
37. Botão **Atualizar HUD** na barra lateral
38. Extração só fica disponível quando o HUD mostra `READY`

### H) Janela ajustável

39. A janela pode ser **redimensionada** (arraste os cantos ou bordas)
40. Tamanho mínimo reduzido para ecrãs pequenos (880×520)

### I) Exportação manual

41. **CSV filtrado** — colunas escolhidas
42. **Emails .txt** — 1 email por linha (ficheiro leve)
43. **SQLite (.db)** — base de dados completa
44. **CSV completo** — todas as colunas
45. **Só emails** — email, empresa, cnpj, uf
46. **Marketing** — formato Mailchimp/Brevo (com aviso legal LGPD/RGPD)
47. **Guardar na pasta** — exportação direta sem diálogo

### J) Validação extra (opcional)

48. **Validar domínio DNS/MX** — verifica se o domínio tem servidor de correio
49. Não verifica se a caixa de correio existe (isso requer serviços pagos)

### K) O que o programa NÃO faz

50. **Não envia emails** — só extrai e exporta
51. **Não recolhe os seus dados** — corre 100% no seu PC
52. **Não garante** que todos os sites permitem extração (alguns bloqueiam)
53. Proxies gratuitos podem ser **lentos** — VPN paga manual é mais fiável

---

## 2. Painel HUD — o que mostra?

Ao abrir o separador **📊 Extrair**, vê um painel escuro com letras azuis (estilo rádio de carro):

```
╔══════════════════════════════════════════════════════╗
║  PRIVACY HUD  │  SYS: READY                          ║
╠══════════════════════════════════════════════════════╣
║  IP REAL .......... 85.xxx.xxx.xxx  [Lisboa / PT]    ║
║  HIDE IP .......... [ON ]                            ║
║  IP SITES ......... 47.xxx.xxx.xxx  [Frankfurt / DE] ║
║  STATUS ........... IP OCULTO — OK                   ║
╠──────────────────────────────────────────────────────╣
║  BROWSER .......... CHROME 1920x1080                 ║
║  IDIOMA ........... pt-PT                            ║
║  DIGITAL .......... RANDOMIZADO                      ║
╚══════════════════════════════════════════════════════╝
```

| Linha | Significado |
|-------|-------------|
| **IP REAL** | O IP da sua internet (casa/escritório) |
| **HIDE IP [ON]** | Proteção de IP ativa |
| **IP SITES** | O IP que os sites veem durante a extração |
| **STATUS** | `IP OCULTO — OK` = IPs diferentes, a funcionar |
| **BROWSER / IDIOMA** | Impressão digital randomizada enviada aos sites |
| **SYS** | `CALIBRANDO` → `SCANNING` → `READY` |

**Aguarde `READY` antes de clicar Iniciar Extração.**

### Hide My IP — integrado

**Sim.** Igual à extensão **Hide My IP** do Chrome, mas **dentro do programa** — não precisa instalar nada à parte.

| O que faz | Como |
|-----------|------|
| **Ocultar IP** | Ligado por defeito — os sites não veem o IP da sua casa |
| **Painel HUD** | Mostra tudo visualmente antes de extrair |
| **Randomizar browser** | User-Agent, idioma, resolução aleatórios |
| **Desativar** | Desmarque «Ocultar IP» na barra lateral |

### Nota sobre MAC

O **MAC da placa de rede nunca é enviado à internet**. O HUD mostra o que realmente muda: **IP** e **impressão digital do browser**.

### Preciso instalar VPN ou extensão Chrome?

**Não.** Tudo funciona dentro do `CompanyEmailExtractor.exe`.

### Opções avançadas (proxy manual — opcional)

Existem VPNs gratuitas (ProtonVPN free, Windscribe free, etc.), mas:

- Limites de dados e velocidade
- Menos servidores
- Nem todas oferecem proxy SOCKS5/HTTP
- Qualidade e privacidade variam

**VPNs pagas** (NordVPN, Mullvad, ProtonVPN Plus, Surfshark…) costumam oferecer proxy SOCKS5 nas definições — mais fiáveis para uso regular.

### Como configurar no software

1. Instale e ligue a **sua VPN** (app separada — não vem no software)
2. Nas definições da VPN, procure **SOCKS5 proxy** ou **HTTP proxy**
3. No software: **Privacidade** → escolha **Proxy / VPN (ocultar IP)**
4. Cole o endereço, ex: `socks5://127.0.0.1:1080`
5. Inicie a extração

### O que a VPN NÃO faz

- Não torna ilegal → legal
- Não elimina responsabilidade no uso dos dados (RGPD/LGPD)
- Não substitui consentimento para email marketing

---

## 3. Instalação Windows

### Método recomendado — Setup.exe

1. Descarregue: **CompanyEmailExtractor-Setup.exe**
   - https://github.com/tiagosgama90-coder/web_scraping/releases/latest
2. Duplo clique no instalador
3. **Seguinte → Instalar → Concluir**
4. Abra pelo **Menu Iniciar**

O instalador inclui:
- `CompanyEmailExtractor.exe` — o programa
- `COMO_USAR.md` — este guia
- `LEIA-ME.txt` — resumo rápido

### Pastas de trabalho (criadas automaticamente)

```
Documentos\CompanyEmailExtractor\
  downloads\     ← ZIPs Receita Federal (Brasil)
  export\        ← CSV, TXT, SQLite exportados
```

---

## 4. Interface — cada opção explicada

### Barra lateral

| Opção | O que faz |
|-------|-----------|
| **País** | PT, BR, ES, FR, DE, IT, GB, MX, AR, CO, CL, PE, US, CA, NL, BE, PL, RO, OUTRO |
| **Fonte de dados** | FIZ, Receita Federal, Empresite, diretórios, fontes personalizadas |
| **Modo** | `limitado` = teste / `automatico` = extração completa |
| **Limite** | `50` = teste / `0` = sem limite |
| **Campos a exportar** | Marcar colunas desejadas |
| **Obrigatório ter e-mail** | Só exporta com email válido |
| **Validar DNS/MX** | Verifica servidor de correio do domínio |
| **Dividir exportação** | Ficheiros de N linhas (1000 predefinido) |
| **Gravar enquanto extrai** | CSV/TXT em tempo real |
| **SQLite em tempo real** | Base de dados durante extração |
| **Anti-Bot** | Playwright + Cloudflare |
| **Painel HUD** | Separador Extrair — IP real, IP oculto, país, estado |
| **Hide My IP** | Ligado por defeito — desmarque para IP normal |
| **🔍 Pré-visualizar** | Amostra na tabela sem gravar |
| **▶ Iniciar Extração** | Extração completa + gravação |
| **⏹ Parar** | Para e mantém o que já foi gravado |

### Separadores

| Separador | Conteúdo |
|-----------|----------|
| **📊 Extrair** | Tabela, progresso, botões de exportação |
| **🌍 Diretórios** | Bases de dados por país — botão **Usar** |
| **➕ Minhas Fontes** | Adicionar sites personalizados |
| **📖 Guia** | Ajuda integrada |

---

## 5. Como usar — passo a passo

### Teste rápido (2 minutos) — Portugal

1. País: **PT**
2. Fonte: **★ Diretório FIZ**
3. Modo: **limitado**, Limite: **50**
4. Privacidade: **Direta** (ou Proxy se tiver VPN)
5. **🔍 Pré-visualizar** (25) → ver emails na tabela
6. **▶ Iniciar Extração** se estiver OK

### Brasil — milhões de emails

1. País: **BR**, Fonte: **★ Receita Federal**
2. UF: **Todos**, marque **Extrair UF por UF**
3. Modo: **automatico**, Limite: **0**
4. Ative: **Gravar enquanto extrai**, **SQLite**
5. **▶ Iniciar Extração**
6. Resultados em `Documentos\CompanyEmailExtractor\export\`

### Qualquer país com diretórios

1. Separador **🌍 Diretórios** → escolha país → **Usar**
2. **Pré-visualizar** (25)
3. **Iniciar Extração**

### Site personalizado

1. Separador **➕ Minhas Fontes**
2. Cole URL → **Adicionar e usar**
3. **Iniciar Extração**

---

## 6. Países e fontes disponíveis

| País | Fonte principal | Tipo |
|------|-----------------|------|
| 🇧🇷 Brasil | Receita Federal | Dados oficiais abertos |
| 🇵🇹 Portugal | FIZ | Diretório público |
| 🇪🇸 Espanha | Empresite | Sitemap (~4M empresas) |
| 🇫🇷 França | Societe.com, Pages Jaunes | Diretórios |
| 🇩🇪 Alemanha | Gelbe Seiten, North Data | Diretórios |
| 🇮🇹 Itália | Pagine Gialle | Diretórios |
| 🇬🇧 Reino Unido | Yell.com | Diretórios |
| 🇲🇽 México | Sección Amarilla | Guias locais |
| 🇦🇷 Argentina | Guía de Empresas | Diretórios |
| 🇨🇴 Colômbia | Páginas Amarillas | Guias locais |
| 🇨🇱 Chile | Amarillas.cl | Guias locais |
| 🇵🇪 Peru | Páginas Amarillas | Guias locais |
| 🇺🇸 EUA | Yellow Pages, Manta | Diretórios |
| 🇨🇦 Canadá | Yellow Pages CA | Guias locais |
| 🇳🇱 Holanda | Detelefoongids | Diretórios |
| 🇧🇪 Bélgica | Golden Pages | Diretórios |
| 🇵🇱 Polónia | Panorama Firm | Diretórios |
| 🇷🇴 Roménia | ListaFirme | Diretórios |

---

## 7. Formatos de exportação

| Formato | Extensão | Uso |
|---------|----------|-----|
| CSV filtrado | `.csv` | Excel, LibreOffice |
| Emails texto | `.txt` | 1 email por linha |
| SQLite | `.db` | DB Browser for SQLite |
| Marketing | `.csv` | Mailchimp, Brevo (com aviso legal) |

Durante extração (automático em `export\`):
- `parte_0001.csv`, `parte_0002.csv`… (1000 linhas cada)
- `emails_0001.txt`
- `empresas.db`

---

## 8. Onde ficam os ficheiros

```
Documentos\CompanyEmailExtractor\
  downloads\          ← ZIPs Receita Federal
  export\
    empresas_br_...\  ← pasta por extração
      UF_SP\          ← Brasil UF por UF
      parte_0001.csv
      emails_0001.txt
      empresas.db
```

Fontes personalizadas guardadas em:
```
C:\Users\SeuNome\AppData\Local\CompanyEmailExtractor\custom_sources.json
```

---

## 9. Problemas comuns

| Problema | Solução |
|----------|---------|
| 0 resultados | Modo limitado, limite 50, Anti-Bot ON |
| Site bloqueado | Ativar Anti-Bot; ou usar Proxy/VPN |
| Proxy não funciona | Verificar endereço; VPN ligada |
| ZIP corrompido (BR) | **🗑 Limpar ZIPs corrompidos** + re-download |
| Excel não abre ficheiro grande | Usar `parte_0001.csv` (1000 linhas) |
| Como abrir .db | DB Browser for SQLite (sqlitebrowser.org) |

---

## 10. Avisos legais

- Use os dados em conformidade com **LGPD** (Brasil) e **RGPD** (Portugal/Europa)
- **Não envie emails em massa** sem consentimento do destinatário
- Respeite os **termos de uso** dos sites
- O programa **extrai dados** — não envia emails
- VPN/Proxy **oculta IP técnico** — não elimina responsabilidade legal
- Priorize fontes **oficiais** (Receita Federal, FIZ) quando possível

---

## Ligações

| Recurso | URL |
|---------|-----|
| Download Setup | https://github.com/tiagosgama90-coder/web_scraping/releases/latest |
| Código fonte | https://github.com/tiagosgama90-coder/web_scraping |

---

*Company Email Extractor v2.15.0 — Guia do utilizador*

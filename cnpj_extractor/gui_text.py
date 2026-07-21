GUIDE_TEXT = """
BEM-VINDO AO COMPANY EMAIL EXTRACTOR
===================================

Este guia explica passo a passo como extrair e-mails de empresas
de qualquer país, site ou base de dados.


PASSO 1 — ESCOLHER A BASE DE DADOS
-----------------------------------
Na barra lateral esquerda, use o menu «Base de dados / Diretório».
Todas as bases de TODOS os países estão na mesma lista:

  • 🇵🇹 FIZ Portugal — ~490.000 empresas
  • 🇧🇷 Receita Federal — ~67 milhões
  • 🇪🇸 Empresite — ~4 milhões
  • 🇫🇷 Societe.com, Pages Jaunes…
  • 🇩🇪 Gelbe Seiten, North Data…
  • E mais 15+ países

Ao escolher uma base, o país é ajustado automaticamente.
O menu «País» serve sobretudo para filtros (UF, distrito, setor).


PASSO 2 — MODO E LIMITE
------------------------
  • Limitado = teste rápido (recomendado para começar)
  • Automático = extração completa (pode demorar horas)
  • Limite: 50 para teste, 0 para sem limite


PASSO 3 — FONTES PERSONALIZADAS
--------------------------------
  • Separador «Minhas Fontes» → cole URL → «Adicionar e usar»
  • Ou «➕ Adicionar nova fonte...» no menu de bases

Tipos de fonte personalizada:

┌─────────────────────────────────────────────────────────┐
│ SITEMAP XML                                             │
│ Cole: https://site.com/sitemap.xml                      │
│ O software descobre TODAS as páginas automaticamente.   │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ LISTA DE URLS — um link por linha ou ficheiro .txt      │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ PÁGINA / SITE — segue links no mesmo domínio            │
└─────────────────────────────────────────────────────────┘


PASSO 4 — INICIAR / PARAR / PRÉ-VISUALIZAR
-------------------------------------------
No separador «Extrair», logo ABAIXO do painel HUD, há três botões GRANDES:

  ▶ INICIAR EXTRAÇÃO  — começa a extração completa
  ⏹ PARAR             — interrompe a extração
  🔍 Pré-visualizar    — vê amostra na tabela (não grava ficheiros)

Aguarde SYS: READY no HUD antes de clicar.

EM BAIXO do ecrã há o painel «ATIVIDADE EM TEMPO REAL»:
  • Mostra o que o software está a fazer (descobrir sitemaps, anti-bot, etc.)
  • Lista cada empresa/email capturado à medida que aparece
  • Indica erros e quando a extração termina


PASSO 5 — PAINEL HUD + HIDE MY IP
----------------------------------
No separador «Extrair» ha um PAINEL ESCURO com letras AZUIS
(estilo radio de carro) — o HUD de privacidade:

  • IP REAL — o seu IP com pais/cidade
  • HIDE IP [ON] — protecao ativa
  • IP SITES — o IP que os sites veem
  • STATUS — IP OCULTO — OK quando funciona
  • BROWSER / IDIOMA — impressao digital randomizada

Aguarde SYS: READY antes de extrair.

Na barra lateral:
  • Ocultar IP (ativado por defeito)
  • Randomizar impressao digital do browser
  • Botao «Atualizar HUD»


PASSO 5b — JANELA AJUSTÁVEL
-----------------------------
A janela do programa pode ser redimensionada (arraste os cantos).


PASSO 6 — FILTROS E CAMPOS
---------------------------
Na barra lateral pode escolher:
  • Campos a exportar (email, empresa, cnpj, telefone, uf, etc.)
  • Obrigatório ter e-mail / telefone / CNPJ
  • Validar domínio DNS/MX (verifica se o domínio tem servidor de email)
  • Guardar CSV filtrado automaticamente ao concluir
  • Gravar ficheiros ENQUANTO extrai (não espera pelo fim)
  • SQLite em tempo real para volumes enormes (10M+)
  • Brasil: Extrair UF por UF (pasta SP, RJ, MG…)
  • Filtro por setor: CNAE (BR), CAE/ISIC (PT), ISIC (outros)
  • Vários códigos: 62, 47, 86 — prefixo funciona (62 inclui 6201, 6202…)


PASSO 7 — PRÉ-VISUALIZAR E EXPORTAR
------------------------------------
  1. Configure base, modo e filtros
  2. Clique «🔍 Pré-visualizar» (número = quantos registos, ex: 25)
  3. Os emails aparecem na TABELA
  4. Se estiver OK → «▶ INICIAR EXTRAÇÃO»
  5. Ficheiros guardados em tempo real na pasta de exportação


PASSO 8 — BOTÕES DE EXPORTAÇÃO
-------------------------------
  CSV filtrado, SQLite, emails .txt, Marketing — na parte inferior do ecrã


ADICIONAR NOVO SITE RAPIDAMENTE
--------------------------------
  • Separador "Minhas Fontes" → cole o URL → "Adicionar e usar"
  • Usa anti-bot automaticamente com as mesmas configurações
  • Ou "+ Adicionar Fonte" para opções avançadas (sitemap, lista URLs)


INSTALACAO WINDOWS (SETUP.EXE)
-------------------------------
  • Execute installer\build_setup.bat para criar CompanyEmailExtractor-Setup.exe
  • Ou descarregue do GitHub Actions (artifact CompanyEmailExtractor-Installer)
  • Alternativa: INSTALAR.bat (Python portátil, sem instalar no sistema)


EXEMPLOS RÁPIDOS
----------------

Portugal (teste 2 min):
  País: PT | Fonte: FIZ | Modo: limitado | Limite: 50
  Hide My IP: ATIVADO (predefinição)

Portugal (completo):
  País: PT | Fonte: FIZ | Modo: automático | Limite: 0

Espanha (teste rápido):
  Base: 🇪🇸 Empresite → Pré-visualizar: 25 → INICIAR EXTRAÇÃO

Brasil (milhões):
  País: BR | Fonte: Receita Federal | UF: Todos | Modo: automático
  Limite: 0 | Gravar enquanto extrai: ON


ONDE FICAM OS FICHEIROS
------------------------
  Documentos\\CompanyEmailExtractor\\
    downloads\\  — ZIPs Receita Federal (Brasil)
    export\\     — CSV, TXT, SQLite exportados


PROBLEMAS COMUNS
----------------
  • 0 resultados → Modo limitado, limite 50, Anti-Bot ON
  • Site bloqueado → Hide My IP já vem ativo; aguarde preparação
  • Hide My IP falhou → tente de novo em 1 minuto
  • Excel não abre ficheiro grande → usar parte_0001.csv (1000 linhas)


AVISOS LEGAIS
-------------
  • Use em conformidade com LGPD (Brasil) e RGPD (Portugal/Europa)
  • Não envie emails em massa sem consentimento
  • O programa extrai dados — não envia emails
"""

ADD_SOURCE_HELP = """
TIPOS DE FONTE:

• sitemap — URL de um sitemap XML (descobre páginas automaticamente)
• urls — Lista de URLs (uma por linha ou ficheiro .txt)
• page — Uma página ou site (segue links no mesmo domínio)

DICA: Para sites grandes, use o tipo «sitemap» se o site tiver sitemap.xml.
"""

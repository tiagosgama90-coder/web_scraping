GUIDE_TEXT = """
BEM-VINDO AO COMPANY EMAIL EXTRACTOR
===================================

Este guia explica passo a passo como extrair e-mails de empresas
de qualquer país, site ou base de dados.


PASSO 1 — ESCOLHER O PAÍS
--------------------------
Na barra lateral, escolha:
  • PT = Portugal
  • BR = Brasil
  • OUTRO = qualquer outro país/site


PASSO 2 — ESCOLHER A FONTE
---------------------------
Fontes pré-definidas:
  • Diretório FIZ (Portugal) — ~490.000 empresas
  • Receita Federal (Brasil) — ~67 milhões de empresas
  • DadosBrasil API (Brasil) — consultas rápidas

Fontes personalizadas (qualquer site):
  • Vá ao separador "Minhas Fontes"
  • Clique em "+ Adicionar Fonte"
  • Escolha o tipo e cole o URL


PASSO 3 — TIPOS DE FONTE PERSONALIZADA
---------------------------------------

┌─────────────────────────────────────────────────────────┐
│ SITEMAP XML                                             │
│ Cole: https://site.com/sitemap.xml                      │
│         ou https://site.com/api/sitemap/empresas/1      │
│ O software descobre TODAS as páginas automaticamente.   │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ LISTA DE URLS                                           │
│ Cole um link por linha:                                 │
│   https://site.com/empresa-1                            │
│   https://site.com/empresa-2                            │
│ Ou importe um ficheiro .txt com os links.               │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ PÁGINA / SITE                                           │
│ Cole o URL de uma página ou site:                       │
│   https://site.com/empresas                             │
│ Modo automático: segue links no mesmo site.             │
└─────────────────────────────────────────────────────────┘


PASSO 4 — MODO DE EXTRAÇÃO
---------------------------
  • Limitado = teste rápido (recomendado para começar)
  • Automático = extração completa (pode demorar horas)


PASSO 5 — FILTROS E CAMPOS
---------------------------
Na barra lateral pode escolher:
  • Campos a exportar (email, empresa, cnpj, telefone, uf, etc.)
  • Obrigatório ter e-mail / telefone / CNPJ
  • Validar domínio DNS/MX (verifica se o domínio tem servidor de email)
  • Guardar CSV filtrado automaticamente ao concluir


PASSO 6 — INICIAR E EXPORTAR
-----------------------------
  1. Clique "▶ Iniciar Extração"
  2. Veja os resultados na tabela
  3. O CSV filtrado é guardado na pasta de exportação (se ativo)
  4. Ou use: CSV filtrado | Guardar na pasta | Só emails | Marketing


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

Portugal (completo):
  País: PT | Fonte: FIZ | Modo: automático | Limite: 0

Site qualquer (sitemap):
  Minhas Fontes → + Adicionar → Tipo: Sitemap
  URL: https://diretorio.fiz.co/sitemap.xml

Site qualquer (página):
  Minhas Fontes → + Adicionar → Tipo: Página
  URL: https://exemplo.com/contactos


DICAS
-----
  • Comece sempre com limite 10-50 para testar
  • Nem todas as empresas têm e-mail registado
  • Respeite os termos de uso dos sites
  • Use os dados em conformidade com RGPD/LGPD


PROBLEMAS?
----------
  • 0 resultados → teste com limite 10, modo limitado
  • Site bloqueado → alguns sites têm proteção anti-bot
  • Muito lento → normal no modo automático completo
"""

ADD_SOURCE_HELP = """
TIPOS DE FONTE:

• Sitemap XML — para sites com sitemap (descobre páginas sozinho)
  Exemplo: https://site.com/sitemap.xml

• Lista de URLs — cole links diretos (um por linha)
  Exemplo: https://site.com/empresa-123

• Página/Site — uma URL; modo auto segue links no mesmo site
  Exemplo: https://site.com/diretorio
"""

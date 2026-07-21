GUIDE_TEXT = """
BEM-VINDO AO COMPANY EMAIL EXTRACTOR
===================================

Este guia explica passo a passo como extrair e-mails de empresas
de qualquer país, site ou base de dados.


PASSO 1 — ESCOLHER O PAÍS
--------------------------
Na barra lateral, escolha o país:
  • PT = Portugal (FIZ — ~490k empresas)
  • BR = Brasil (Receita Federal — ~67M empresas)
  • ES, FR, DE, IT, GB = Europa (diretórios empresariais)
  • MX, AR, CO, CL, PE = América Latina
  • US, CA = América do Norte
  • NL, BE, PL, RO = mais países europeus
  • OUTRO = qualquer site personalizado

Separador «🌍 Diretórios» — lista TODAS as bases por país.


PASSO 2 — ESCOLHER A FONTE
---------------------------
Fontes oficiais / principais:
  • 🇵🇹 FIZ Portugal — ~490.000 empresas (sitemap)
  • 🇧🇷 Receita Federal — ~67 milhões (dados abertos)
  • 🇪🇸 Empresite — ~4 milhões (sitemap Espanha)

Diretórios por país (separador «Diretórios»):
  • 🇫🇷 França: Societe.com, Pages Jaunes, Pappers…
  • 🇩🇪 Alemanha: Gelbe Seiten, North Data, WLW…
  • 🇮🇹 Itália: Pagine Gialle, Kompass…
  • 🇬🇧 Reino Unido: Yell.com, Kompass UK…
  • 🇲🇽 México: Sección Amarilla, DENUE…
  • 🇦🇷 Argentina, 🇨🇴 Colômbia, 🇨🇱 Chile, 🇵🇪 Peru
  • 🇺🇸 EUA: Yellow Pages, Manta…
  • 🇨🇦 Canadá, 🇳🇱 Holanda, 🇧🇪 Bélgica, 🇵🇱 Polónia, 🇷🇴 Roménia

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


PASSO 5 — PRIVACIDADE (SUA ESCOLHA)
------------------------------------
Na secção «🔒 Privacidade — ligação e identidade»:

  • Direta (IP normal) — ligação normal, predefinição
  • 🌐 Ocultar IP (automático — gratuito) — estilo Hide My IP:
      o software procura proxies gratuitos sozinho (1 clique)
  • Proxy / VPN (manual) — tráfego pela VPN que VOCÊ configurar
  • 🎭 Ocultar MAC / ID máquina / impressão digital — valores falsos

COMO USAR «OCULTAR IP» (GRATUITO):
  1. Escolha «🌐 Ocultar IP (automático — gratuito)»
  2. Clique Pré-visualizar ou Iniciar Extração
  3. Aguarde 30–60 s enquanto testa proxies
  4. Quando encontrar um funcional, a extração começa com IP oculto

  • 🎭 Ocultar MAC / ID máquina / impressão digital — valores falsos

IMPORTANTE sobre MAC: sites na internet NÃO recebem o MAC da sua placa
de rede. Esta opção randomiza a impressão digital visível nos pedidos HTTP.

NOTA: proxies gratuitos podem ser mais lentos. VPN manual é mais fiável.


PASSO 5b — JANELA AJUSTÁVEL
-----------------------------
A janela do programa pode ser redimensionada (arraste os cantos).
Reduza ou aumente o tamanho conforme o seu ecrã.


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


PASSO 7 — PRÉ-VISUALIZAR
-------------------------
Antes de gravar ficheiros, pode ver o que o software captou:

  1. Configure país, fonte e filtros
  2. Clique «🔍 Pré-visualizar» (número = quantos registos ver, ex: 25)
  3. Os emails aparecem na TABELA do separador «Extrair»
  4. NÃO grava CSV/SQLite na pré-visualização
  5. Se estiver OK → clique «▶ Iniciar Extração» para extração completa


PASSO 8 — INICIAR E EXPORTAR
-----------------------------
  1. Clique "▶ Iniciar Extração"
  2. Veja os resultados na tabela
  3. Os ficheiros são guardados EM TEMPO REAL na pasta de exportação
  4. CSV em partes de 1000 linhas + SQLite + emails .txt
  5. Brasil com "Todos": extrai UF por UF automaticamente


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

Espanha (teste rápido):
  Separador «Diretórios» → Espanha → Empresite → Usar
  Pré-visualizar: 25 → ver emails no ecrã

França (teste):
  Diretórios → França → Societe.com → Usar → Pré-visualizar 25

Alemanha (teste):
  Diretórios → Alemanha → Gelbe Seiten → Usar → Pré-visualizar 25

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

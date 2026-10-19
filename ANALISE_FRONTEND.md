# R-Mobile (RestovicTrips) — Auditoria e Documentação do Frontend

> **Status:** Concluído e Sincronizado  
> **Data:** 19/10/2026  
> **Tema:** Bootstrap 5.3 + R-Mobile Brand Kit (Roxo `#5e03fc` / `#22015c`)

---

## 1. Arquitetura e Ordem de Carregamento de Estilos (Cascata)

A aplicação segue rigorosamente a cascata do kit de marca para sobrescrever os padrões do Bootstrap sem hacks inline:

```
1. Google Fonts (Inter: 400, 600, 700, 800)
       ↓
2. Bootstrap 5.3.3 CSS (CDN com integridade SRI)
       ↓
3. rmobile.css (Tokens de cor, tipografia e botões da marca R-Mobile)
       ↓
4. style.css (Ajustes de hero banner, cards de métricas e encadeamento hash)
       ↓
5. Bootstrap 5.3.3 Bundle JS (Antes do fechamento do </body>)
```

---

## 2. Paleta de Cores e Kit de Marca (R-Mobile)

| Token CSS | Cor HEX | Função no Sistema |
| :--- | :--- | :--- |
| `--rm-brand-950` | `#22015c` | Navbar principal, cabeçalhos de tabela (`table-brand`) e início do gradiente Hero |
| `--rm-brand-800` | `#4302b0` | Estados ativos de clique |
| `--rm-brand-700` | `#5002d6` | Hover em botões e cor secundária do gradiente |
| `--rm-brand-600` / `--bs-primary` | `#5e03fc` | **Cor Primária da Marca**: botões, links, anéis de foco e badges |
| `--rm-brand-500` | `#8438ff` | Primária em tema escuro e fim do gradiente Hero |
| `--rm-brand-100` | `#ece5ff` | Fundo de ícones e badges sutis (`bg-primary-subtle`) |
| `--bs-success` | `#047857` | Confirmação de cobertura e badges de status ocupado |
| `--bs-danger` | `#dc2626` | Alerta de colisões no hash e botões de remoção |
| `--bs-secondary` | `#475569` | Textos secundários, botões de cancelamento |

---

## 3. Estrutura de Telas e Componentes

### 3.1 Layout Base (`templates/base.html`)
- **Favicon & Brand Icon:** SVG vetorial dedicado (`static/r-mobile-icon.svg`) com chip eSIM estilizado e ondas de rádio.
- **Navbar Responsiva:** Fundo escuro com `--rm-brand-950`, collapse para mobile, links com marcação ativa (`{% if request.endpoint == '...' %}active{% endif %}`).
- **Theme Switcher:** Alternador de tema Claro/Escuro funcional com persistência no `localStorage` via atributo `data-bs-theme`.
- **Alertas Flash:** Dismissíveis nativos do Bootstrap.
- **Rodapé Institucional:** Padronizado com créditos acadêmicos.

### 3.2 Página Inicial (`templates/index.html`)
- **Hero Aconchegante:** Gradiente de marca com cantos arredondados, pílula de destaque, tipografia `display-4` e botões de chamada rápida (CTA).
- **Cards de Funcionalidades:** Três cartões com cantos arredondados `rounded-4`, ícones semânticos em círculos sutis e botões de acesso rápido alinhados.

### 3.3 Formulário de Cadastro (`templates/cadastro.html`)
- **Contenção Visual:** Centralizado em desktop com `col-lg-7`.
- **Usabilidade:** Campo de código do país com transformação automática para maiúsculas (`text-transform: uppercase`), rótulos semânticos e botão de submissão unificado na cor primária da marca (`btn-primary`).

### 3.4 Consulta de Cobertura com Modal (`templates/consulta.html`)
- **Entrada:** Campo de busca com valor preservado após submissão (`value="{{ request.form.get('codigo', '') }}"`).
- **Modal Bootstrap:** Aberto automaticamente após requisição POST quando há resultado. Contém cabeçalho com gradiente da marca, ícone SVG, crachá de confirmação de rede e dados detalhados da operadora/tecnologia.
- **Card de Resumo:** Card fixo na página para reabrir o modal caso o usuário o feche sem querer.

### 3.5 Catálogo de Países (`templates/paises.html`)
- **Tabela da Marca (`.table-brand`):** Cabeçalho com `--rm-brand-950` e borda inferior roxa da marca.
- **Botões Compactos (`.btn-sm`):** Botões ajustados para 32px de altura mínima, corrigindo o esticamento vertical anterior.
- **Ações:** Atalho "+ Cadastrar País" no topo e diálogo de confirmação seguro na remoção.

### 3.6 Edição de País (`templates/editar.html`)
- **Chave Primária Protegida:** Campo do código desabilitado com aviso didático sobre imutabilidade da chave hash.
- **Ergonomia:** Alinhado ao layout de cadastro com botões Salvar (`btn-primary`) e Cancelar (`btn-outline-secondary`).

### 3.7 Painel de Monitoramento Hash (`templates/estatisticas.html`)
- **Cartões de Métricas:** 4 cartões com fundos sutis (`bg-primary-subtle` e `bg-danger-subtle`) destacando Capacidade, Registros, Fator de Carga e Colisões.
- **Métricas Algorítmicas:** Exibição de Buckets Ocupados, Total de Comparações em Busca e Operações Totais calculadas pelo backend.
- **Visualização das Cadeias:** Macro recursiva Jinja exibindo a dispersão nos buckets e listas encadeadas com código e nome do país associado.

---

## 4. Inconsistências Identificadas e Sanadas

1. **Inchaço de Botões Pequenos:** A regra genérica `.btn { min-height: 44px; }` em `rmobile.css` deformava botões dentro de tabelas. Foi adicionada a regra `.btn-sm { min-height: 32px; font-size: 0.875rem; padding: 0.25rem 0.65rem; }`.
2. **Cores Genéricas em Cabeçalhos:** Removido o `.table-dark` padrão do Bootstrap e criado o `.table-brand thead` estilizado com a cor da marca.
3. **Inconsistência de Botões de Ação:** O botão de cadastro era verde (`btn-success`) e o de edição roxo (`btn-primary`). Todos os envios de formulário foram unificados no roxo da marca R-Mobile (`btn-primary`).
4. **Perda de Busca na Consulta:** O input de consulta limpava o código digitado. Agora mantém o termo pesquisado.
5. **Acessibilidade do Modal:** Se o modal fosse fechado, o resultado desaparecia da tela. Foi adicionado um card inline que permite reabrir o modal a qualquer momento.
6. **Contraste no Dark Mode:** Variáveis de ícones e tabelas foram revisadas para manter legibilidade tanto em tema claro quanto escuro.
7. **SVG Faltante:** Criado o arquivo `static/r-mobile-icon.svg` com a especificação visual do kit de marca.

---

## 5. Como Testar e Visualizar

```bash
# Ativar ambiente virtual e executar Flask
source venv/bin/activate
python app.py
```
Acesse `http://127.0.0.1:5000` no seu navegador.

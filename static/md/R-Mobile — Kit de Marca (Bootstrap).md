[Código](#codigo)

# Kit de Marca

Internet móvel por eSIM para viajantes. Identidade em roxo #5e03fc, pronta para Bootstrap 5.3 — celular e computador, claro e escuro.

## Logotipo

Estilo de operadora: cor chapada, letra R pesada dentro de um chip de eSIM (canto cortado), ondas de sinal e wordmark todo em peso 800. Marca original, criada para trabalho acadêmico sem fins comerciais.

### Ícone (favicon / app)

### Regras

**Pode:** respiro mínimo igual à metade do ícone · wordmark com no mínimo 96 px · versão branca sobre roxo ou escuro.

**Evite:** distorcer ou girar · trocar o roxo · aplicar sobre foto sem escurecer o fundo.

## Cores

Principal **#5e03fc** (brand-600), com escala 50–950 no formato do Tailwind. Toque para copiar o HEX.

### Papéis no Bootstrap

Info e warning continuam com os padrões do Bootstrap. No tema escuro, o primário passa a ser #8438ff.

Branco sobre #5e03fc · 7,2:1 primary-subtle

## Tipografia

Inter com fallback do sistema, aplicada por `--bs-body-font-family`. Use as classes nativas.

Display 4 .display-4 · 800

# Título h1

## Título h2

### Título h3

Texto de destaque (.lead) para introduções.

Texto base de 16 px para parágrafos e formulários.

Texto pequeno (.small .text-secondary) para legendas.

## Componentes Bootstrap

Botões com 44 px de altura, cantos de .75 rem e cartões de 1 rem.

AtivoCobertura disponívelExpira em 3 diaseSIM inativo5G

##### Consulta de cobertura

Código do país

**COBERTURA DISPONÍVEL**\
Itália · Europa · Operadora IT · 5G

##### Europa Plus

Ativo

10 GB · 30 dias

6,2 GB

| Código | País | Tec. |
| --- | --- | --- |
| BR | Brasil | 5G |
| PT | Portugal | 5G |
| JP | Japão | 4G |

- «
- 1
- [2](#componentes)
- [3](#componentes)
- [»](#componentes)

## Usar no projeto Flask

Opção A: Bootstrap por CDN + `rmobile.css`. Opção B: recompilar com SCSS.

### templates/base.html

```

```

### static/css/rmobile.css (tema completo)

```

```

### Opção B: custom.scss

```

```

R-Mobile · marca fictícia criada para trabalho acadêmico, sem fins comerciais.

[![]({{%20url_for%28%27static%27,%20filename=%27r-mobile-icon.svg%27%29%20}}) R-Mobile]({{%20url_for%28%27index%27%29%20}})

{% block content %}{% endblock %}

\`, scss:\`// custom.scss — compile com: sass custom.scss static/css/rmobile.css $primary: #5e03fc; $secondary: #475569; $success: #047857; $danger: #dc2626; $font-family-sans-serif: Inter, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; $border-radius: .75rem; $btn-font-weight: 600; $headings-font-weight: 700; @import "bootstrap/scss/bootstrap";\`}; code.ov2=document.getElementById('ov').textContent.trim(); for(const k of \['base','ov2','scss'\])document.getElementById(k).textContent=code\[k\]; async function copy(t,b){try{await navigator.clipboard.writeText(t);if(b){const o=b.textContent;b.textContent='Copiado!';setTimeout(()=>b.textContent=o,1200)}}catch(e){}} document.addEventListener('click',e=>{const s=e.target.closest('.sw');if(s)copy(s.dataset.h);const c=e.target.closest('\[data-c\]');if(c)copy(code\[c.dataset.c\],c)}); document.getElementById('theme').onclick=()=>{const r=document.documentElement;r.setAttribute('data-bs-theme',r.getAttribute('data-bs-theme')==='dark'?'light':'dark')};
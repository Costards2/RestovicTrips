from flask import Flask, render_template, request, redirect, url_for, flash
from tabela_hash import TabelaHash
from b_tree import ArvoreB
import persistencia
import os

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'chave_secreta_padrao_segura')

# ==============================================================================
# INICIALIZAÇÃO DAS ESTRUTURAS DE DADOS
# ==============================================================================
# 1. Tabela Hash (Países e Cobertura - Etapa 1)
tabela = TabelaHash()
dados_iniciais = persistencia.carregar_dados()
for p in dados_iniciais:
    tabela.inserir(p['codigo'], p)

# 2. Árvore B (Clientes e eSIMs - Etapa 2)
arvore_clientes = ArvoreB(ordem=5)


def carregar_clientes_na_arvore(arvore: ArvoreB = None) -> ArvoreB:
    """Carrega os clientes a partir do arquivo JSON na Árvore B de forma idempotente."""
    alvo = arvore if arvore is not None else arvore_clientes
    clientes = persistencia.carregar_clientes()
    alvo.carregar(clientes)
    return alvo


# Carga idempotente na Árvore B ao subir a aplicação
carregar_clientes_na_arvore(arvore_clientes)

# 3. Pacotes de Serviço (Etapa 2)
pacotes = persistencia.carregar_pacotes()
mapa_pacotes = persistencia.obter_mapa_pacotes()


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        codigo = request.form.get('codigo').strip().upper()
        dados = {
            "codigo": codigo,
            "pais": request.form.get('pais').strip(),
            "regiao": request.form.get('regiao').strip(),
            "operadora": request.form.get('operadora').strip(),
            "tecnologia": request.form.get('tecnologia').strip()
        }
        if tabela.inserir(codigo, dados):
            persistencia.salvar_dados(tabela)
            flash('País cadastrado com sucesso!', 'success')
            return redirect(url_for('paises'))
        else:
            flash('Erro: Código já cadastrado.', 'danger')
    return render_template('cadastro.html')

@app.route('/consulta', methods=['GET', 'POST'])
def consulta():
    resultado = None
    if request.method == 'POST':
        codigo = request.form.get('codigo').strip()
        resultado = tabela.buscar(codigo)
        if not resultado:
            flash('País não encontrado ou sem cobertura.', 'danger')
    return render_template('consulta.html', resultado=resultado)

@app.route('/paises')
def paises():
    lista = tabela.listar_todos()
    return render_template('paises.html', paises=lista)

@app.route('/editar/<codigo>', methods=['GET', 'POST'])
def editar(codigo):
    pais = tabela.buscar(codigo)
    if not pais:
        flash('País não encontrado.', 'danger')
        return redirect(url_for('paises'))
        
    if request.method == 'POST':
        novos_dados = {
            "pais": request.form.get('pais').strip(),
            "regiao": request.form.get('regiao').strip(),
            "operadora": request.form.get('operadora').strip(),
            "tecnologia": request.form.get('tecnologia').strip()
        }
        if tabela.alterar(codigo, novos_dados):
            persistencia.salvar_dados(tabela)
            flash('Dados atualizados com sucesso!', 'success')
        else:
            flash('Erro ao atualizar.', 'danger')
        return redirect(url_for('paises'))
        
    return render_template('editar.html', pais=pais)

@app.route('/remover/<codigo>', methods=['POST'])
def remover(codigo):
    if tabela.remover(codigo):
        persistencia.salvar_dados(tabela)
        flash('País removido com sucesso!', 'success')
    else:
        flash('Erro ao remover o país.', 'danger')
    return redirect(url_for('paises'))

@app.route('/estatisticas')
def estatisticas():
    stats = tabela.obter_estatisticas()
    return render_template('estatisticas.html', stats=stats, tabela=tabela.tabela)

if __name__ == '__main__':
    app.run(debug=True)

from flask import Flask, render_template, request, redirect, url_for, flash
import os
from datetime import datetime
from werkzeug.utils import secure_filename
from typing import Dict, List, Any

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'  # Chave secreta para flash messages

# Configurações para upload de arquivos
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Simulação de banco de dados
vagas_cadastradas: List[Dict[str, Any]] = []
acoes_cadastradas: List[Dict[str, Any]] = []

def allowed_file(filename: str) -> bool:
    """Verifica se a extensão do arquivo é permitida"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def salvar_vaga(dados_pessoais: Dict[str, Any],
                dados_contato: Dict[str, Any],
                dados_profissionais: Dict[str, Any],
                dados_bancarios: Dict[str, Any],
                termos: Dict[str, bool],
                arquivos: Dict[str, str]) -> bool:
    """Salva os dados da vaga no banco de dados simulado"""
    vaga = {
        'dados_pessoais': dados_pessoais,
        'dados_contato': dados_contato,
        'dados_profissionais': dados_profissionais,
        'dados_bancarios': dados_bancarios,
        'termos': termos,
        'arquivos': arquivos,
        'data_cadastro': datetime.now()
    }
    vagas_cadastradas.append(vaga)
    return True

# Rotas principais
@app.route('/')
def index():
    """Rota principal da aplicação"""
    return render_template('homepage.html')

@app.route('/cadastrar-material', methods=['GET', 'POST'])
def cadastrar_material():
    if request.method == 'POST':
        # Processar os dados do formulário aqui
        pass
    return render_template('cadastrar_material.html')

@app.route('/cadastrar-cliente', methods=['GET', 'POST'])
def cadastrar_cliente():
    if request.method == 'POST':
        # Processar os dados do formulário aqui
        pass
    return render_template('cadastrar_cliente.html')

@app.route('/cadastrar-acao', methods=['GET', 'POST'])
def cadastrar_acao():
    if request.method == 'POST':
        try:
            nova_acao = {
                'nome': request.form.get('nome', ''),
                'tipo': request.form.get('tipo', ''),
                'descricao': request.form.get('descricao', ''),
                'data_inicio': request.form.get('data_inicio', ''),
                'data_fim': request.form.get('data_fim', ''),
                'responsavel': request.form.get('responsavel', ''),
                'local': request.form.get('local', ''),
                'data_cadastro': datetime.now()
            }
            acoes_cadastradas.append(nova_acao)
            flash('Ação cadastrada com sucesso!', 'success')
            return redirect(url_for('banco_acoes'))
        except Exception as e:
            flash(f'Erro ao cadastrar ação: {str(e)}', 'danger')
    return render_template('cadastrar_acao.html')

@app.route('/cadastrar-vaga', methods=['GET', 'POST'])
def cadastrar_vaga():
    if request.method == 'POST':
        try:
            # Dados Pessoais
            dados_pessoais = {
                'nome_completo': request.form.get('nome_completo', ''),
                'data_nascimento': request.form.get('data_nascimento', ''),
                'estado_civil': request.form.get('estado_civil', ''),
                'dependentes': int(request.form.get('dependentes', 0)),
                'nacionalidade': request.form.get('nacionalidade', ''),
                'cpf': request.form.get('cpf', '')
            }

            # Dados de Contato
            dados_contato = {
                'telefone': request.form.get('telefone', ''),
                'email': request.form.get('email', ''),
                'cep': request.form.get('cep', ''),
                'cidade': request.form.get('cidade', ''),
                'estado': request.form.get('estado', '')
            }

            # Dados Profissionais
            dados_profissionais = {
                'area_atuacao': request.form.get('area_atuacao', ''),
                'tipo_interesse': request.form.get('tipo_interesse', ''),
                'disponibilidade': request.form.get('disponibilidade', ''),
                'experiencia': request.form.get('experiencia', '')
            }

            # Dados Bancários
            dados_bancarios = {
                'banco': request.form.get('banco', ''),
                'agencia': request.form.get('agencia', ''),
                'conta': request.form.get('conta', ''),
                'pix': request.form.get('pix', '')
            }

            # Termos Legais
            termos = {
                'lgpd': request.form.get('lgpd') == 'on',
                'processos_seletivos': request.form.get('processos_seletivos') == 'on'
            }

            # Processar upload de arquivos
            arquivos: Dict[str, str] = {}
            for field in ['foto', 'rg', 'cpf_doc', 'titulo_eleitor', 'ctps', 'certificacoes']:
                if field in request.files:
                    file = request.files[field]
                    if file and allowed_file(file.filename):
                        filename = secure_filename(f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
                        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                        arquivos[field] = filename

            salvar_vaga(dados_pessoais, dados_contato, dados_profissionais, dados_bancarios, termos, arquivos)
            flash('Cadastro de vaga realizado com sucesso!', 'success')
            return redirect(url_for('banco_vagas'))

        except Exception as e:
            flash(f'Erro ao cadastrar vaga: {str(e)}', 'danger')

    return render_template('cadastrar_vaga.html')

# Rotas para bancos de dados
@app.route('/banco-clientes')
def banco_clientes():
    clientes: List[Dict[str, Any]] = []
    return render_template('banco_clientes.html', clientes=clientes)

@app.route('/banco-materiais')
def banco_materiais():
    materiais: List[Dict[str, Any]] = []
    return render_template('banco_materiais.html', materiais=materiais)

@app.route('/banco-vagas')
def banco_vagas():
    try:
        return render_template('banco_vagas.html', vagas=vagas_cadastradas)
    except Exception as e:
        app.logger.error(f"Erro em banco_vagas: {str(e)}")
        flash('Ocorreu um erro ao acessar o banco de vagas', 'danger')
        return redirect(url_for('index'))

@app.route('/banco-acoes')
def banco_acoes():
    return render_template('banco_acoes.html', acoes=acoes_cadastradas)

# Rotas para detalhes
@app.route('/vaga/<int:vaga_id>')
def detalhes_vaga(vaga_id: int):
    try:
        vaga = vagas_cadastradas[vaga_id]
        return render_template('detalhes_vaga.html', vaga=vaga, vaga_id=vaga_id)
    except IndexError:
        flash('Vaga não encontrada', 'danger')
        return redirect(url_for('banco_vagas'))

@app.route('/acao/<int:acao_id>')
def detalhes_acao(acao_id: int):
    try:
        acao = acoes_cadastradas[acao_id]
        return render_template('detalhes_acao.html', acao=acao, acao_id=acao_id)
    except IndexError:
        flash('Ação não encontrada', 'danger')
        return redirect(url_for('banco_acoes'))

# Rotas para edição
@app.route('/editar-acao/<int:acao_id>', methods=['GET', 'POST'])
def editar_acao(acao_id: int):
    try:
        if 0 <= acao_id < len(acoes_cadastradas):
            acao = acoes_cadastradas[acao_id]

            if request.method == 'POST':
                acao['nome'] = request.form.get('nome', acao.get('nome', ''))
                acao['tipo'] = request.form.get('tipo', acao.get('tipo', ''))
                acao['descricao'] = request.form.get('descricao', acao.get('descricao', ''))
                acao['data_inicio'] = request.form.get('data_inicio', acao.get('data_inicio', ''))
                acao['data_fim'] = request.form.get('data_fim', acao.get('data_fim', ''))
                acao['responsavel'] = request.form.get('responsavel', acao.get('responsavel', ''))
                acao['local'] = request.form.get('local', acao.get('local', ''))

                flash('Ação atualizada com sucesso!', 'success')
                return redirect(url_for('detalhes_acao', acao_id=acao_id))

            return render_template('editar_acao.html', acao=acao, acao_id=acao_id)
        else:
            flash('Ação não encontrada', 'danger')
            return redirect(url_for('banco_acoes'))

    except Exception as e:
        flash(f'Erro ao editar ação: {str(e)}', 'danger')
        return redirect(url_for('banco_acoes'))

# Rota para exclusão
@app.route('/excluir-acao/<int:acao_id>', methods=['POST'])
def excluir_acao(acao_id: int):
    try:
        if 0 <= acao_id < len(acoes_cadastradas):
            acao_removida = acoes_cadastradas.pop(acao_id)
            flash(f'Ação "{acao_removida.get("nome", "sem nome")}" excluída com sucesso!', 'success')
        else:
            flash('Ação não encontrada para exclusão', 'danger')
    except Exception as e:
        flash(f'Erro ao excluir ação: {str(e)}', 'danger')

    return redirect(url_for('banco_acoes'))

# Inicialização
if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)
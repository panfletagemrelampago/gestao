from flask import Flask, render_template, request, redirect, url_for, flash, session
import os
from datetime import datetime
from werkzeug.utils import secure_filename
from typing import Dict, List, Any

app = Flask(__name__)
app.secret_key = '@Zadu0204#='

# Configurações
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf', 'doc', 'docx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Credenciais
PREDEFINED_CREDENTIALS = {
    'username': 'Relam01',
    'password': '@Zadu0204#='
}

# Armazenamento de dados
vagas_cadastradas: List[Dict[str, Any]] = []
acoes_cadastradas: List[Dict[str, Any]] = []
materiais_cadastrados: List[Dict[str, Any]] = []
clientes_cadastrados: List[Dict[str, Any]] = []

def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def handle_file_upload(file, prefix):
    if file and allowed_file(file.filename):
        filename = secure_filename(f"{prefix}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return filename
    return None

@app.before_request
def require_login():
    allowed_routes = ['login', 'static']
    if request.endpoint not in allowed_routes and not session.get('logged_in'):
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username == PREDEFINED_CREDENTIALS['username'] and password == PREDEFINED_CREDENTIALS['password']:
            session['logged_in'] = True
            session['username'] = username
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Credenciais inválidas. Tente novamente.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    flash('Você foi desconectado.', 'success')
    return redirect(url_for('login'))

@app.route('/')
def index():
    return render_template('index.html')

# Rotas para Clientes
@app.route('/clientes')
def banco_clientes():
    return render_template('banco_clientes.html', clientes=clientes_cadastrados)

@app.route('/clientes/cadastrar', methods=['GET', 'POST'])
def cadastrar_cliente():
    if request.method == 'POST':
        try:
            cliente = {
                'id': len(clientes_cadastrados) + 1,
                'nome': request.form['nome_cliente'],
                'empresa': request.form['empresa'],
                'segmento': request.form['segmento'],
                'telefone': request.form['telefone'],
                'email': request.form['email'],
                'cpf_cnpj': request.form['cpf_cnpj']
            }
            clientes_cadastrados.append(cliente)
            flash('Cliente cadastrado com sucesso!', 'success')
            return redirect(url_for('banco_clientes'))
        except Exception as e:
            flash(f'Erro ao cadastrar cliente: {str(e)}', 'danger')
    return render_template('cadastrar_cliente.html')

@app.route('/clientes/editar/<int:cliente_id>', methods=['GET', 'POST'])
def editar_cliente(cliente_id):
    cliente = next((c for c in clientes_cadastrados if c['id'] == cliente_id), None)
    if not cliente:
        flash('Cliente não encontrado!', 'danger')
        return redirect(url_for('banco_clientes'))

    if request.method == 'POST':
        try:
            cliente.update({
                'nome': request.form['nome_cliente'],
                'empresa': request.form['empresa'],
                'segmento': request.form['segmento'],
                'telefone': request.form['telefone'],
                'email': request.form['email'],
                'cpf_cnpj': request.form['cpf_cnpj']
            })
            flash('Cliente atualizado com sucesso!', 'success')
            return redirect(url_for('banco_clientes'))
        except Exception as e:
            flash(f'Erro ao atualizar cliente: {str(e)}', 'danger')
    return render_template('editar_cliente.html', cliente=cliente)

@app.route('/clientes/excluir/<int:cliente_id>')
def excluir_cliente(cliente_id):
    try:
        global clientes_cadastrados
        clientes_cadastrados = [c for c in clientes_cadastrados if c['id'] != cliente_id]
        flash('Cliente excluído com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao excluir cliente: {str(e)}', 'danger')
    return redirect(url_for('banco_clientes'))

# Rotas para Materiais
@app.route('/materiais')
def banco_materiais():
    return render_template('banco_materiais.html', materiais=materiais_cadastrados)

@app.route('/materiais/cadastrar', methods=['GET', 'POST'])
def cadastrar_material():
    if request.method == 'POST':
        try:
            documento = handle_file_upload(request.files.get('documento'), 'doc')
            amostra = handle_file_upload(request.files.get('amostra'), 'img')

            novo_material = {
                'id': len(materiais_cadastrados) + 1,
                'empresa': request.form['empresa'],
                'quantidade': int(request.form['quantidade']),
                'data_inicio': datetime.strptime(request.form['data_inicio'], '%Y-%m-%d').date(),
                'data_termino': datetime.strptime(request.form['data_termino'], '%Y-%m-%d').date(),
                'nome_campanha': request.form['nome_campanha'],
                'responsavel': request.form['responsavel'],
                'documento_url': documento,
                'imagem_url': amostra,
                'data_cadastro': datetime.now()
            }
            materiais_cadastrados.append(novo_material)
            flash('Material cadastrado com sucesso!', 'success')
            return redirect(url_for('banco_materiais'))
        except Exception as e:
            flash(f'Erro ao cadastrar material: {str(e)}', 'danger')
    return render_template('cadastrar_material.html')

@app.route('/materiais/editar/<int:material_id>', methods=['GET', 'POST'])
def editar_material(material_id):
    material = next((m for m in materiais_cadastrados if m['id'] == material_id), None)
    if not material:
        flash('Material não encontrado!', 'danger')
        return redirect(url_for('banco_materiais'))

    if request.method == 'POST':
        try:
            material.update({
                'empresa': request.form['empresa'],
                'quantidade': int(request.form['quantidade']),
                'data_inicio': datetime.strptime(request.form['data_inicio'], '%Y-%m-%d').date(),
                'data_termino': datetime.strptime(request.form['data_termino'], '%Y-%m-%d').date(),
                'nome_campanha': request.form['nome_campanha'],
                'responsavel': request.form['responsavel']
            })

            for field, prefix in [('documento', 'doc'), ('amostra', 'img')]:
                file = request.files.get(field)
                if file and allowed_file(file.filename):
                    filename = handle_file_upload(file, prefix)
                    if filename:
                        material[f"{'documento' if field == 'documento' else 'imagem'}_url"] = filename

            flash('Material atualizado com sucesso!', 'success')
            return redirect(url_for('banco_materiais'))
        except Exception as e:
            flash(f'Erro ao atualizar material: {str(e)}', 'danger')

    material_edit = material.copy()
    material_edit['data_inicio'] = material['data_inicio'].strftime('%Y-%m-%d')
    material_edit['data_termino'] = material['data_termino'].strftime('%Y-%m-%d')
    return render_template('editar_material.html', material=material_edit)

@app.route('/materiais/excluir/<int:material_id>')
def excluir_material(material_id):
    try:
        global materiais_cadastrados
        material = next((m for m in materiais_cadastrados if m['id'] == material_id), None)
        if material:
            materiais_cadastrados = [m for m in materiais_cadastrados if m['id'] != material_id]
            flash('Material excluído com sucesso!', 'success')
        else:
            flash('Material não encontrado!', 'danger')
    except Exception as e:
        flash(f'Erro ao excluir material: {str(e)}', 'danger')
    return redirect(url_for('banco_materiais'))

# Rotas para Vagas
@app.route('/vagas')
def banco_vagas():
    return render_template('banco_vagas.html', vagas=vagas_cadastradas)

@app.route('/vagas/cadastrar', methods=['GET', 'POST'])
def cadastrar_vaga():
    if request.method == 'POST':
        try:
            vaga = {
                'id': len(vagas_cadastradas) + 1,
                'dados_pessoais': {
                    'nome_completo': request.form.get('nome_completo'),
                    'data_nascimento': request.form.get('data_nascimento'),
                    'cpf': request.form.get('cpf')
                },
                'dados_contato': {
                    'telefone': request.form.get('telefone'),
                    'email': request.form.get('email')
                },
                'dados_profissionais': {
                    'area_atuacao': request.form.get('area_atuacao'),
                    'disponibilidade': request.form.get('disponibilidade'),
                    'experiencia': request.form.get('experiencia')
                },
                'data_cadastro': datetime.now()
            }
            vagas_cadastradas.append(vaga)
            flash('Vaga cadastrada com sucesso!', 'success')
            return redirect(url_for('banco_vagas'))
        except Exception as e:
            flash(f'Erro ao cadastrar vaga: {str(e)}', 'danger')
    return render_template('cadastrar_vaga.html')

@app.route('/vagas/editar/<int:vaga_id>', methods=['GET', 'POST'])
def editar_vaga(vaga_id):
    vaga = next((v for v in vagas_cadastradas if v['id'] == vaga_id), None)
    if not vaga:
        flash('Vaga não encontrada!', 'danger')
        return redirect(url_for('banco_vagas'))

    if request.method == 'POST':
        try:
            vaga.update({
                'dados_pessoais': {
                    'nome_completo': request.form.get('nome_completo', vaga['dados_pessoais']['nome_completo']),
                    'data_nascimento': request.form.get('data_nascimento', vaga['dados_pessoais']['data_nascimento']),
                    'cpf': request.form.get('cpf', vaga['dados_pessoais']['cpf'])
                },
                'dados_contato': {
                    'telefone': request.form.get('telefone', vaga['dados_contato']['telefone']),
                    'email': request.form.get('email', vaga['dados_contato']['email'])
                },
                'dados_profissionais': {
                    'area_atuacao': request.form.get('area_atuacao', vaga['dados_profissionais']['area_atuacao']),
                    'disponibilidade': request.form.get('disponibilidade', vaga['dados_profissionais']['disponibilidade']),
                    'experiencia': request.form.get('experiencia', vaga['dados_profissionais']['experiencia'])
                }
            })
            flash('Vaga atualizada com sucesso!', 'success')
            return redirect(url_for('banco_vagas'))
        except Exception as e:
            flash(f'Erro ao atualizar vaga: {str(e)}', 'danger')
    return render_template('editar_vaga.html', vaga=vaga)

@app.route('/vagas/excluir/<int:vaga_id>')
def excluir_vaga(vaga_id):
    try:
        global vagas_cadastradas
        vagas_cadastradas = [v for v in vagas_cadastradas if v['id'] != vaga_id]
        flash('Vaga excluída com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao excluir vaga: {str(e)}', 'danger')
    return redirect(url_for('banco_vagas'))

# Rotas para Ações
@app.route('/acoes')
def banco_acoes():
    return render_template('banco_acoes.html', acoes=acoes_cadastradas)

@app.route('/acoes/cadastrar', methods=['GET', 'POST'])
def cadastrar_acao():
    if request.method == 'POST':
        try:
            material_filename = handle_file_upload(request.files['material_acao'], 'material')
            foto_filename = handle_file_upload(request.files['foto_equipe'], 'foto')

            nova_acao = {
                'id': len(acoes_cadastradas) + 1,
                'nome_cliente': request.form.get('nome_cliente'),
                'empresa': request.form.get('empresa'),
                'tipo_acao': request.form.get('tipo_acao'),
                'quantidade_material': request.form.get('quantidade'),
                'data_inicio': datetime.strptime(request.form.get('data_inicio'), '%Y-%m-%d').date(),
                'data_termino': datetime.strptime(request.form.get('data_termino'), '%Y-%m-%d').date(),
                'hora_inicio': request.form.get('hora_inicio'),
                'hora_termino': request.form.get('hora_termino'),
                'locais': request.form.get('locais'),
                'quantidade_pessoas': request.form.get('quantidade_pessoas'),
                'responsavel': request.form.get('responsavel'),
                'material_acao': material_filename,
                'foto_equipe': foto_filename,
                'ativa': True,
                'data_cadastro': datetime.now()
            }
            acoes_cadastradas.append(nova_acao)
            flash('Ação cadastrada com sucesso!', 'success')
            return redirect(url_for('banco_acoes'))
        except Exception as e:
            flash(f'Erro ao cadastrar ação: {str(e)}', 'danger')
    return render_template('cadastrar_acao.html')

@app.route('/acoes/editar/<int:acao_id>', methods=['GET', 'POST'])
def editar_acao(acao_id):
    acao = next((a for a in acoes_cadastradas if a['id'] == acao_id), None)
    if not acao:
        flash('Ação não encontrada!', 'danger')
        return redirect(url_for('banco_acoes'))

    if request.method == 'POST':
        try:
            acao.update({
                'nome_cliente': request.form.get('nome_cliente', acao['nome_cliente']),
                'empresa': request.form.get('empresa', acao['empresa']),
                'tipo_acao': request.form.get('tipo_acao', acao['tipo_acao']),
                'quantidade_material': request.form.get('quantidade', acao['quantidade_material']),
                'data_inicio': datetime.strptime(request.form.get('data_inicio'), '%Y-%m-%d').date(),
                'data_termino': datetime.strptime(request.form.get('data_termino'), '%Y-%m-%d').date(),
                'hora_inicio': request.form.get('hora_inicio', acao['hora_inicio']),
                'hora_termino': request.form.get('hora_termino', acao['hora_termino']),
                'locais': request.form.get('locais', acao['locais']),
                'quantidade_pessoas': request.form.get('quantidade_pessoas', acao['quantidade_pessoas']),
                'responsavel': request.form.get('responsavel', acao['responsavel'])
            })

            for field, prefix in [('material_acao', 'material'), ('foto_equipe', 'foto')]:
                file = request.files.get(field)
                if file and allowed_file(file.filename):
                    filename = handle_file_upload(file, prefix)
                    if filename:
                        acao[field] = filename

            flash('Ação atualizada com sucesso!', 'success')
            return redirect(url_for('banco_acoes'))
        except Exception as e:
            flash(f'Erro ao atualizar ação: {str(e)}', 'danger')
    return render_template('editar_acao.html', acao=acao)

@app.route('/acoes/excluir/<int:acao_id>')
def excluir_acao(acao_id):
    try:
        global acoes_cadastradas
        acoes_cadastradas = [a for a in acoes_cadastradas if a['id'] != acao_id]
        flash('Ação excluída com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao excluir ação: {str(e)}', 'danger')
    return redirect(url_for('banco_acoes'))

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)

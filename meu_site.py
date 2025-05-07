from flask import Flask, render_template, request, redirect, url_for, flash
import os
from datetime import datetime
from werkzeug.utils import secure_filename
from typing import Dict, List, Any

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

vagas_cadastradas: List[Dict[str, Any]] = []
acoes_cadastradas: List[Dict[str, Any]] = []
materiais_cadastrados: List[Dict[str, Any]] = []
clientes_cadastrados: List[Dict[str, Any]] = []


def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def salvar_vaga(dados_pessoais, dados_contato, dados_profissionais, dados_bancarios, termos, arquivos):
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


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/cadastrar-material', methods=['GET', 'POST'])
def cadastrar_material():
    if request.method == 'POST':
        try:
            empresa = request.form['empresa']
            quantidade = int(request.form['quantidade'])
            validade_inicio = request.form['validade_inicio']
            validade_fim = request.form['validade_fim']
            campanha = request.form['campanha']
            encarregado = request.form['encarregado']

            documento = request.files['documento']
            filename = None
            if documento and allowed_file(documento.filename):
                filename = secure_filename(f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{documento.filename}")
                documento.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            materiais_cadastrados.append({
                'empresa': empresa,
                'quantidade': quantidade,
                'data_inicio': validade_inicio,
                'data_termino': validade_fim,
                'nome_campanha': campanha,
                'responsavel': encarregado,
                'imagem_url': f"{UPLOAD_FOLDER}/{filename}" if filename else None
            })
            flash('Material cadastrado com sucesso!', 'success')
            return redirect(url_for('banco_materiais'))
        except Exception as e:
            flash(f'Erro ao cadastrar material: {str(e)}', 'danger')
    return render_template('cadastrar_material.html')


@app.route('/cadastrar-cliente', methods=['GET', 'POST'])
def cadastrar_cliente():
    if request.method == 'POST':
        try:
            cliente = {
                'nome': request.form['nome_cliente'],
                'empresa': request.form['empresa'],
                'segmento': request.form['segmento'],
                'telefone': request.form['telefone'],
                'email': request.form['email'],
                'cpf_cnpj': request.form['cpf_cnpj'],
                'id': len(clientes_cadastrados)
            }
            clientes_cadastrados.append(cliente)
            flash('Cliente cadastrado com sucesso!', 'success')
            return redirect(url_for('banco_clientes'))
        except Exception as e:
            flash(f'Erro ao cadastrar cliente: {str(e)}', 'danger')
    return render_template('cadastrar_cliente.html')


@app.route('/editar-cliente/<int:cliente_id>', methods=['GET', 'POST'])
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


@app.route('/excluir-cliente/<int:cliente_id>')
def excluir_cliente(cliente_id):
    try:
        global clientes_cadastrados
        clientes_cadastrados = [c for c in clientes_cadastrados if c['id'] != cliente_id]
        flash('Cliente excluído com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao excluir cliente: {str(e)}', 'danger')
    return redirect(url_for('banco_clientes'))


@app.route('/cadastrar-acao', methods=['GET', 'POST'])
def cadastrar_acao():
    if request.method == 'POST':
        try:
            material_acao = request.files['material_acao']
            foto_equipe = request.files['foto_equipe']

            material_filename = None
            foto_filename = None

            if material_acao and allowed_file(material_acao.filename):
                material_filename = secure_filename(
                    f"material_{datetime.now().strftime('%Y%m%d%H%M%S')}_{material_acao.filename}")
                material_acao.save(os.path.join(app.config['UPLOAD_FOLDER'], material_filename))

            if foto_equipe and allowed_file(foto_equipe.filename):
                foto_filename = secure_filename(
                    f"foto_{datetime.now().strftime('%Y%m%d%H%M%S')}_{foto_equipe.filename}")
                foto_equipe.save(os.path.join(app.config['UPLOAD_FOLDER'], foto_filename))

            # Converter strings de data para objetos date
            data_inicio = datetime.strptime(request.form.get('data_inicio'), '%Y-%m-%d').date() if request.form.get('data_inicio') else None
            data_termino = datetime.strptime(request.form.get('data_termino'), '%Y-%m-%d').date() if request.form.get('data_termino') else None

            nova_acao = {
                'nome': f"{request.form.get('nome_cliente', '')} - {request.form.get('empresa', '')}",
                'nome_cliente': request.form.get('nome_cliente', ''),
                'empresa': request.form.get('empresa', ''),
                'tipo': request.form.get('tipo_acao', ''),
                'tipo_acao': request.form.get('tipo_acao', ''),
                'categoria': request.form.get('categoria', ''),
                'quantidade': request.form.get('quantidade', ''),
                'data_inicio': data_inicio,
                'data_termino': data_termino,
                'hora_inicio': request.form.get('hora_inicio', ''),
                'hora_termino': request.form.get('hora_termino', ''),
                'locais': request.form.get('locais', ''),
                'quantidade_pessoas': request.form.get('quantidade_pessoas', ''),
                'responsavel': request.form.get('responsavel', ''),
                'material_acao': f"{UPLOAD_FOLDER}/{material_filename}" if material_filename else None,
                'foto_equipe': f"{UPLOAD_FOLDER}/{foto_filename}" if foto_filename else None,
                'ativa': True,
                'data_cadastro': datetime.now()
            }
            acoes_cadastradas.append(nova_acao)
            flash('Ação cadastrada com sucesso!', 'success')
            return redirect(url_for('banco_acoes'))
        except Exception as e:
            flash(f'Erro ao cadastrar ação: {str(e)}', 'danger')
    return render_template('cadastrar_acao.html')


@app.route('/editar-acao/<int:acao_id>', methods=['GET', 'POST'])
def editar_acao(acao_id):
    acao = acoes_cadastradas[acao_id] if acao_id < len(acoes_cadastradas) else None
    if not acao:
        flash('Ação não encontrada!', 'danger')
        return redirect(url_for('banco_acoes'))

    if request.method == 'POST':
        try:
            # Converter strings de data para objetos date
            data_inicio = datetime.strptime(request.form.get('data_inicio'), '%Y-%m-%d').date() if request.form.get('data_inicio') else None
            data_termino = datetime.strptime(request.form.get('data_termino'), '%Y-%m-%d').date() if request.form.get('data_termino') else None

            acao.update({
                'nome': f"{request.form.get('nome_cliente', acao['nome_cliente'])} - {request.form.get('empresa', acao['empresa'])}",
                'nome_cliente': request.form.get('nome_cliente', acao['nome_cliente']),
                'empresa': request.form.get('empresa', acao['empresa']),
                'tipo': request.form.get('tipo_acao', acao['tipo_acao']),
                'tipo_acao': request.form.get('tipo_acao', acao['tipo_acao']),
                'categoria': request.form.get('categoria', acao['categoria']),
                'quantidade': request.form.get('quantidade', acao['quantidade']),
                'data_inicio': data_inicio,
                'data_termino': data_termino,
                'hora_inicio': request.form.get('hora_inicio', acao['hora_inicio']),
                'hora_termino': request.form.get('hora_termino', acao['hora_termino']),
                'locais': request.form.get('locais', acao['locais']),
                'quantidade_pessoas': request.form.get('quantidade_pessoas', acao['quantidade_pessoas']),
                'responsavel': request.form.get('responsavel', acao['responsavel'])
            })

            # Atualizar arquivos se novos foram enviados
            if 'material_acao' in request.files:
                file = request.files['material_acao']
                if file and allowed_file(file.filename):
                    filename = secure_filename(f"material_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    acao['material_acao'] = f"{UPLOAD_FOLDER}/{filename}"

            if 'foto_equipe' in request.files:
                file = request.files['foto_equipe']
                if file and allowed_file(file.filename):
                    filename = secure_filename(f"foto_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    acao['foto_equipe'] = f"{UPLOAD_FOLDER}/{filename}"

            flash('Ação atualizada com sucesso!', 'success')
            return redirect(url_for('banco_acoes'))
        except Exception as e:
            flash(f'Erro ao atualizar ação: {str(e)}', 'danger')

    return render_template('editar_acao.html', acao=acao, acao_id=acao_id)


@app.route('/excluir-acao/<int:acao_id>')
def excluir_acao(acao_id):
    try:
        global acoes_cadastradas
        acoes_cadastradas = [a for i, a in enumerate(acoes_cadastradas) if i != acao_id]
        flash('Ação excluída com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao excluir ação: {str(e)}', 'danger')
    return redirect(url_for('banco_acoes'))


@app.route('/detalhes-acao/<int:acao_id>')
def detalhes_acao(acao_id):
    acao = acoes_cadastradas[acao_id] if acao_id < len(acoes_cadastradas) else None
    if not acao:
        flash('Ação não encontrada!', 'danger')
        return redirect(url_for('banco_acoes'))
    return render_template('detalhes_acao.html', acao=acao, acao_id=acao_id)


@app.route('/cadastrar-vaga', methods=['GET', 'POST'])
def cadastrar_vaga():
    if request.method == 'POST':
        try:
            dados_pessoais = {
                'nome_completo': request.form.get('nome_completo', ''),
                'data_nascimento': request.form.get('data_nascimento', ''),
                'estado_civil': request.form.get('estado_civil', ''),
                'dependentes': int(request.form.get('dependentes', 0)),
                'nacionalidade': request.form.get('nacionalidade', ''),
                'cpf': request.form.get('cpf', '')
            }
            dados_contato = {
                'telefone': request.form.get('telefone', ''),
                'email': request.form.get('email', ''),
                'cep': request.form.get('cep', ''),
                'cidade': request.form.get('cidade', ''),
                'estado': request.form.get('estado', '')
            }
            dados_profissionais = {
                'area_atuacao': request.form.get('area_atuacao', ''),
                'tipo_interesse': request.form.get('tipo_interesse', ''),
                'disponibilidade': request.form.get('disponibilidade', ''),
                'experiencia': request.form.get('experiencia', '')
            }
            dados_bancarios = {
                'banco': request.form.get('banco', ''),
                'agencia': request.form.get('agencia', ''),
                'conta': request.form.get('conta', ''),
                'pix': request.form.get('pix', '')
            }
            termos = {
                'lgpd': request.form.get('lgpd') == 'on',
                'processos_seletivos': request.form.get('processos_seletivos') == 'on'
            }
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


@app.route('/editar-vaga/<int:vaga_id>', methods=['GET', 'POST'])
def editar_vaga(vaga_id):
    vaga = vagas_cadastradas[vaga_id] if vaga_id < len(vagas_cadastradas) else None
    if not vaga:
        flash('Vaga não encontrada!', 'danger')
        return redirect(url_for('banco_vagas'))

    if request.method == 'POST':
        try:
            dados_pessoais = {
                'nome_completo': request.form.get('nome_completo', ''),
                'data_nascimento': request.form.get('data_nascimento', ''),
                'estado_civil': request.form.get('estado_civil', ''),
                'dependentes': int(request.form.get('dependentes', 0)),
                'nacionalidade': request.form.get('nacionalidade', ''),
                'cpf': request.form.get('cpf', '')
            }
            dados_contato = {
                'telefone': request.form.get('telefone', ''),
                'email': request.form.get('email', ''),
                'cep': request.form.get('cep', ''),
                'cidade': request.form.get('cidade', ''),
                'estado': request.form.get('estado', '')
            }
            dados_profissionais = {
                'area_atuacao': request.form.get('area_atuacao', ''),
                'tipo_interesse': request.form.get('tipo_interesse', ''),
                'disponibilidade': request.form.get('disponibilidade', ''),
                'experiencia': request.form.get('experiencia', '')
            }
            dados_bancarios = {
                'banco': request.form.get('banco', ''),
                'agencia': request.form.get('agencia', ''),
                'conta': request.form.get('conta', ''),
                'pix': request.form.get('pix', '')
            }
            termos = {
                'lgpd': request.form.get('lgpd') == 'on',
                'processos_seletivos': request.form.get('processos_seletivos') == 'on'
            }

            # Atualizar arquivos se novos foram enviados
            arquivos = vaga['arquivos'].copy()
            for field in ['rg', 'cpf_doc', 'titulo_eleitor', 'ctps', 'certificacoes']:
                if field in request.files:
                    file = request.files[field]
                    if file and allowed_file(file.filename):
                        filename = secure_filename(f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
                        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                        arquivos[field] = filename

            # Atualizar a vaga
            vagas_cadastradas[vaga_id] = {
                'dados_pessoais': dados_pessoais,
                'dados_contato': dados_contato,
                'dados_profissionais': dados_profissionais,
                'dados_bancarios': dados_bancarios,
                'termos': termos,
                'arquivos': arquivos,
                'data_cadastro': vaga['data_cadastro']
            }

            flash('Vaga atualizada com sucesso!', 'success')
            return redirect(url_for('banco_vagas'))
        except Exception as e:
            flash(f'Erro ao atualizar vaga: {str(e)}', 'danger')

    return render_template('editar_vaga.html', vaga=vaga, vaga_id=vaga_id)


@app.route('/excluir-vaga/<int:vaga_id>')
def excluir_vaga(vaga_id):
    try:
        global vagas_cadastradas
        vagas_cadastradas = [v for i, v in enumerate(vagas_cadastradas) if i != vaga_id]
        flash('Vaga excluída com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao excluir vaga: {str(e)}', 'danger')
    return redirect(url_for('banco_vagas'))


@app.route('/banco-clientes')
def banco_clientes():
    return render_template('banco_clientes.html', clientes=clientes_cadastrados)


@app.route('/banco-materiais')
def banco_materiais():
    return render_template('banco_materiais.html', materiais=materiais_cadastrados)


@app.route('/banco-vagas')
def banco_vagas():
    return render_template('banco_vagas.html', vagas=vagas_cadastradas)


@app.route('/banco-acoes')
def banco_acoes():
    return render_template('banco_acoes.html', acoes=acoes_cadastradas)


if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)
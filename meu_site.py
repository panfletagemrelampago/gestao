from flask import Flask, render_template, request, redirect, url_for, flash, session, Response
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime, date
from werkzeug.utils import secure_filename
from enum import Enum
import csv
from io import StringIO
import pandas as pd
from whitenoise import WhiteNoise

app = Flask(__name__)
app.config['SECRET_KEY'] = '@Zadu0204#'
app.secret_key = '@Zadu0204#'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
app.wsgi_app = WhiteNoise(app.wsgi_app, root='static/')

# Configurações de upload
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf', 'doc', 'docx', 'csv', 'xlsx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Credenciais
PREDEFINED_CREDENTIALS = {
    'username': 'Relam',
    'password': '@Zadu0204'
}


class StatusAcao(Enum):
    ATIVO = 'ativo'
    INATIVO = 'inativo'
    CONCLUIDO = 'concluido'
    CANCELADO = 'cancelado'

    @classmethod
    def get_by_value(cls, value):
        value_lower = value.lower()
        for status in cls:
            if status.value == value_lower:
                return status
        raise ValueError(f"'{value}' is not a valid StatusAcao")


# Modelos do banco de dados
class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    empresa = db.Column(db.String(100))
    segmento = db.Column(db.String(50))
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    cpf_cnpj = db.Column(db.String(20))
    data_cadastro = db.Column(db.DateTime, default=datetime.now)


class Material(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    empresa = db.Column(db.String(100), nullable=False)
    quantidade = db.Column(db.Integer)
    data_inicio = db.Column(db.Date)
    data_termino = db.Column(db.Date)
    nome_campanha = db.Column(db.String(100))
    responsavel = db.Column(db.String(100))
    documento_url = db.Column(db.String(200))
    imagem_url = db.Column(db.String(200))
    data_cadastro = db.Column(db.DateTime, default=datetime.now)


class Vaga(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dados_pessoais = db.Column(db.JSON)
    dados_contato = db.Column(db.JSON)
    dados_profissionais = db.Column(db.JSON)
    dados_bancarios = db.Column(db.JSON)
    arquivos = db.Column(db.JSON)
    data_cadastro = db.Column(db.DateTime, default=datetime.now)


class Acao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome_cliente = db.Column(db.String(100), nullable=False)
    empresa = db.Column(db.String(100))
    tipo_acao = db.Column(db.String(50))
    quantidade_material = db.Column(db.String(20))
    data_inicio = db.Column(db.Date)
    data_termino = db.Column(db.Date)
    hora_inicio = db.Column(db.String(10))
    hora_termino = db.Column(db.String(10))
    locais = db.Column(db.String(200))
    quantidade_pessoas = db.Column(db.String(10))
    responsavel = db.Column(db.String(100))
    status = db.Column(db.String(20), default='ativo')
    material_acao = db.Column(db.String(200))
    foto_equipe = db.Column(db.String(200))
    data_cadastro = db.Column(db.DateTime, default=datetime.now)


# Criar banco de dados no contexto da aplicação
with app.app_context():
    db.create_all()


def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def handle_file_upload(file, prefix):
    if file and allowed_file(file.filename):
        original_name = secure_filename(file.filename)
        filename = f"{prefix}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{original_name}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return filename
    return None


def calcular_idade(data_nascimento):
    if isinstance(data_nascimento, str):
        try:
            data_nascimento = datetime.strptime(data_nascimento, '%Y-%m-%d').date()
        except ValueError:
            return "N/A"

    hoje = date.today()
    idade = hoje.year - data_nascimento.year - ((hoje.month, hoje.day) < (data_nascimento.month, data_nascimento.day))
    return idade


# Adiciona a função ao contexto do Jinja2
app.jinja_env.globals.update(calcular_idade=calcular_idade)


@app.before_request
def require_login():
    if request.endpoint in [None, 'static', 'login', 'logout']:
        return
    if not session.get('logged_in'):
        return redirect(url_for('login'))


def migrate_status_values():
    with app.app_context():
        try:
            backup_exists = db.engine.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='acao_backup'"
            ).fetchone() is not None

            if not backup_exists:
                db.engine.execute('ALTER TABLE acao RENAME TO acao_backup')
                db.create_all()
                db.engine.execute('''
                    INSERT INTO acao (id, nome_cliente, empresa, tipo_acao, quantidade_material, 
                                    data_inicio, data_termino, hora_inicio, hora_termino, 
                                    locais, quantidade_pessoas, responsavel, status, 
                                    material_acao, foto_equipe, data_cadastro)
                    SELECT id, nome_cliente, empresa, tipo_acao, quantidade_material, 
                           data_inicio, data_termino, hora_inicio, hora_termino, 
                           locais, quantidade_pessoas, responsavel, 
                           LOWER(status),
                           material_acao, foto_equipe, data_cadastro
                    FROM acao_backup
                ''')
                print("Migração de status concluída com sucesso!")
        except Exception as e:
            print(f"Erro durante a migração: {str(e)}")
            db.engine.execute('DROP TABLE IF EXISTS acao')
            db.engine.execute('ALTER TABLE acao_backup RENAME TO acao')
            raise


# Rotas de Autenticação
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
    clientes = Cliente.query.order_by(Cliente.data_cadastro.desc()).all()
    return render_template('banco_clientes.html', clientes=clientes)


@app.route('/clientes/cadastrar', methods=['GET', 'POST'])
def cadastrar_cliente():
    if request.method == 'POST':
        try:
            novo_cliente = Cliente(
                nome=request.form['nome_cliente'],
                empresa=request.form['empresa'],
                segmento=request.form['segmento'],
                telefone=request.form['telefone'],
                email=request.form['email'],
                cpf_cnpj=request.form['cpf_cnpj']
            )
            db.session.add(novo_cliente)
            db.session.commit()
            flash('Cliente cadastrado com sucesso!', 'success')
            return redirect(url_for('banco_clientes'))
        except Exception as cliente_error:
            db.session.rollback()
            flash(f'Erro ao cadastrar cliente: {str(cliente_error)}', 'danger')
    return render_template('cadastrar_cliente.html')


@app.route('/clientes/editar/<int:cliente_id>', methods=['GET', 'POST'])
def editar_cliente(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)

    if request.method == 'POST':
        try:
            cliente.nome = request.form['nome_cliente']
            cliente.empresa = request.form['empresa']
            cliente.segmento = request.form['segmento']
            cliente.telefone = request.form['telefone']
            cliente.email = request.form['email']
            cliente.cpf_cnpj = request.form['cpf_cnpj']
            db.session.commit()
            flash('Cliente atualizado com sucesso!', 'success')
            return redirect(url_for('banco_clientes'))
        except Exception as update_error:
            db.session.rollback()
            flash(f'Erro ao atualizar cliente: {str(update_error)}', 'danger')
    return render_template('editar_cliente.html', cliente=cliente)


@app.route('/clientes/excluir/<int:cliente_id>', methods=['POST'])
def excluir_cliente(cliente_id):
    try:
        cliente = Cliente.query.get_or_404(cliente_id)
        db.session.delete(cliente)
        db.session.commit()
        flash('Cliente excluído com sucesso!', 'success')
    except Exception as delete_error:
        db.session.rollback()
        flash(f'Erro ao excluir cliente: {str(delete_error)}', 'danger')
    return redirect(url_for('banco_clientes'))


@app.route('/clientes/importar', methods=['GET', 'POST'])
def importar_clientes():
    if request.method == 'POST':
        try:
            if 'arquivo' not in request.files:
                flash('Nenhum arquivo enviado', 'danger')
                return redirect(request.url)

            file = request.files['arquivo']
            if file.filename == '':
                flash('Nenhum arquivo selecionado', 'danger')
                return redirect(request.url)

            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)

                if filename.endswith('.csv'):
                    stream = StringIO(file.stream.read().decode("UTF8"), newline=None)
                    csv_reader = csv.DictReader(stream, delimiter=',')
                    clientes_data = [row for row in csv_reader]

                elif filename.endswith('.xlsx'):
                    df = pd.read_excel(file)
                    clientes_data = df.to_dict('records')

                else:
                    flash('Formato de arquivo não suportado', 'danger')
                    return redirect(request.url)

                count = 0
                for cliente_data in clientes_data:
                    try:
                        novo_cliente = Cliente(
                            nome=cliente_data.get('nome', ''),
                            empresa=cliente_data.get('empresa', ''),
                            segmento=cliente_data.get('segmento', ''),
                            telefone=cliente_data.get('telefone', ''),
                            email=cliente_data.get('email', ''),
                            cpf_cnpj=cliente_data.get('cpf_cnpj', '')
                        )
                        db.session.add(novo_cliente)
                        count += 1
                    except Exception as e:
                        db.session.rollback()
                        flash(f'Erro ao processar linha: {str(e)}', 'warning')
                        continue

                db.session.commit()
                flash(f'{count} clientes importados com sucesso!', 'success')
                return redirect(url_for('banco_clientes'))

        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao importar clientes: {str(e)}', 'danger')
            app.logger.error(f"Erro na importação: {str(e)}", exc_info=True)

    return redirect(url_for('banco_clientes'))


@app.route('/clientes/download-modelo')
def download_modelo_clientes():
    output = StringIO()
    writer = csv.writer(output)

    writer.writerow(['nome', 'empresa', 'segmento', 'telefone', 'email', 'cpf_cnpj'])
    writer.writerow(['João Silva', 'Empresa A', 'Tecnologia', '11999999999', 'joao@empresa.com', '123.456.789-00'])
    writer.writerow(['Maria Souza', 'Empresa B', 'Educação', '21988888888', 'maria@empresa.com', '987.654.321-00'])

    output.seek(0)
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=modelo_clientes.csv"}
    )


# Rotas para Materiais
@app.route('/materiais')
def banco_materiais():
    materiais = Material.query.order_by(Material.data_cadastro.desc()).all()
    return render_template('banco_materiais.html', materiais=materiais)


@app.route('/materiais/cadastrar', methods=['GET', 'POST'])
def cadastrar_material():
    if request.method == 'POST':
        try:
            documento = handle_file_upload(request.files.get('documento'), 'doc')
            amostra = handle_file_upload(request.files.get('amostra'), 'img')

            novo_material = Material(
                empresa=request.form['empresa'],
                quantidade=int(request.form['quantidade']),
                data_inicio=datetime.strptime(request.form['data_inicio'], '%Y-%m-%d').date(),
                data_termino=datetime.strptime(request.form['data_termino'], '%Y-%m-%d').date(),
                nome_campanha=request.form['nome_campanha'],
                responsavel=request.form['responsavel'],
                documento_url=documento,
                imagem_url=amostra
            )
            db.session.add(novo_material)
            db.session.commit()
            flash('Material cadastrado com sucesso!', 'success')
            return redirect(url_for('banco_materiais'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao cadastrar material: {str(e)}', 'danger')
    return render_template('cadastrar_material.html')


@app.route('/materiais/editar/<int:material_id>', methods=['GET', 'POST'])
def editar_material(material_id):
    material = Material.query.get_or_404(material_id)

    if request.method == 'POST':
        try:
            material.empresa = request.form['empresa']
            material.quantidade = int(request.form['quantidade'])
            material.data_inicio = datetime.strptime(request.form['data_inicio'], '%Y-%m-%d').date()
            material.data_termino = datetime.strptime(request.form['data_termino'], '%Y-%m-%d').date()
            material.nome_campanha = request.form['nome_campanha']
            material.responsavel = request.form['responsavel']

            if 'documento' in request.files and request.files['documento'].filename:
                documento = handle_file_upload(request.files['documento'], 'doc')
                if documento:
                    material.documento_url = documento

            if 'amostra' in request.files and request.files['amostra'].filename:
                amostra = handle_file_upload(request.files['amostra'], 'img')
                if amostra:
                    material.imagem_url = amostra

            db.session.commit()
            flash('Material atualizado com sucesso!', 'success')
            return redirect(url_for('banco_materiais'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar material: {str(e)}', 'danger')

    material_edit = {
        'id': material.id,
        'empresa': material.empresa,
        'quantidade': material.quantidade,
        'data_inicio': material.data_inicio.strftime('%Y-%m-%d'),
        'data_termino': material.data_termino.strftime('%Y-%m-%d'),
        'nome_campanha': material.nome_campanha,
        'responsavel': material.responsavel,
        'documento_url': material.documento_url,
        'imagem_url': material.imagem_url
    }

    return render_template('editar_material.html', material=material_edit)


@app.route('/materiais/excluir/<int:material_id>', methods=['POST'])
def excluir_material(material_id):
    try:
        material = Material.query.get_or_404(material_id)
        db.session.delete(material)
        db.session.commit()
        flash('Material excluído com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir material: {str(e)}', 'danger')
    return redirect(url_for('banco_materiais'))


# Rotas para Vagas
@app.route('/vagas')
def banco_vagas():
    vagas = Vaga.query.order_by(Vaga.data_cadastro.desc()).all()
    return render_template('banco_vagas.html', vagas=vagas)


@app.route('/vagas/cadastrar', methods=['GET', 'POST'])
def cadastrar_vaga():
    if request.method == 'POST':
        try:
            dias_disponibilidade = request.form.getlist('disponibilidade[]')

            arquivos = {
                'rg': handle_file_upload(request.files.get('rg'), 'rg'),
                'cpf_doc': handle_file_upload(request.files.get('cpf_doc'), 'cpf'),
                'titulo_eleitor': handle_file_upload(request.files.get('titulo_eleitor'), 'titulo'),
                'ctps': handle_file_upload(request.files.get('ctps'), 'ctps')
            }

            nova_vaga = Vaga(
                dados_pessoais={
                    'nome_completo': request.form['nome_completo'],
                    'data_nascimento': request.form['data_nascimento'],
                    'cpf': request.form['cpf'],
                    'estado_civil': request.form.get('estado_civil', ''),
                    'dependentes': request.form.get('dependentes', '')
                },
                dados_contato={
                    'telefone': request.form['telefone'],
                    'email': request.form['email'],
                    'cep': request.form.get('cep', ''),
                    'cidade': request.form.get('cidade', ''),
                    'estado': request.form.get('estado', '')
                },
                dados_profissionais={
                    'area_atuacao': request.form['area_atuacao'],
                    'tipo_interesse': request.form.get('tipo_interesse', ''),
                    'disponibilidade': ', '.join(dias_disponibilidade),
                    'experiencia': request.form['experiencia']
                },
                dados_bancarios={
                    'banco': request.form.get('banco', ''),
                    'agencia': request.form.get('agencia', ''),
                    'conta': request.form.get('conta', ''),
                    'pix': request.form.get('pix', '')
                },
                arquivos=arquivos
            )

            db.session.add(nova_vaga)
            db.session.commit()
            flash('Vaga cadastrada com sucesso!', 'success')
            return redirect(url_for('banco_vagas'))

        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao cadastrar vaga: {str(e)}', 'danger')
            app.logger.error(f"Erro ao cadastrar vaga: {str(e)}", exc_info=True)
            return render_template('cadastrar_vaga.html')

    return render_template('cadastrar_vaga.html')


@app.route('/vagas/editar/<int:vaga_id>', methods=['GET', 'POST'])
def editar_vaga(vaga_id):
    vaga = Vaga.query.get_or_404(vaga_id)

    if request.method == 'POST':
        try:
            # Obter os dados do formulário
            dias_disponibilidade = request.form.getlist('disponibilidade[]')

            # Processar arquivos (se enviados)
            arquivos = {
                'rg': handle_file_upload(request.files.get('rg'), 'rg') or vaga.arquivos.get('rg'),
                'cpf_doc': handle_file_upload(request.files.get('cpf_doc'), 'cpf') or vaga.arquivos.get('cpf_doc'),
                'titulo_eleitor': handle_file_upload(request.files.get('titulo_eleitor'),
                                                     'titulo') or vaga.arquivos.get('titulo_eleitor'),
                'ctps': handle_file_upload(request.files.get('ctps'), 'ctps') or vaga.arquivos.get('ctps')
            }

            # Atualizar os dados
            vaga.dados_pessoais = {
                'nome_completo': request.form['nome_completo'],
                'data_nascimento': request.form['data_nascimento'],
                'cpf': request.form['cpf'],
                'estado_civil': request.form.get('estado_civil', vaga.dados_pessoais.get('estado_civil', '')),
                'dependentes': request.form.get('dependentes', vaga.dados_pessoais.get('dependentes', ''))
            }

            vaga.dados_contato = {
                'telefone': request.form.get('telefone', vaga.dados_contato.get('telefone', '')),
                'email': request.form.get('email', vaga.dados_contato.get('email', '')),
                'cep': request.form.get('cep', vaga.dados_contato.get('cep', '')),
                'cidade': request.form.get('cidade', vaga.dados_contato.get('cidade', '')),
                'estado': request.form.get('estado', vaga.dados_contato.get('estado', ''))
            }

            vaga.dados_profissionais = {
                'area_atuacao': request.form.get('area_atuacao', vaga.dados_profissionais.get('area_atuacao', '')),
                'tipo_interesse': request.form.get('tipo_interesse',
                                                   vaga.dados_profissionais.get('tipo_interesse', '')),
                'disponibilidade': ', '.join(dias_disponibilidade),
                'experiencia': request.form.get('experiencia', vaga.dados_profissionais.get('experiencia', ''))
            }

            vaga.dados_bancarios = {
                'banco': request.form.get('banco', vaga.dados_bancarios.get('banco', '')),
                'agencia': request.form.get('agencia', vaga.dados_bancarios.get('agencia', '')),
                'conta': request.form.get('conta', vaga.dados_bancarios.get('conta', '')),
                'pix': request.form.get('pix', vaga.dados_bancarios.get('pix', ''))
            }

            vaga.arquivos = arquivos

            db.session.commit()
            flash('Vaga atualizada com sucesso!', 'success')
            return redirect(url_for('banco_vagas'))

        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar vaga: {str(e)}', 'danger')
            return redirect(url_for('editar_vaga', vaga_id=vaga_id))

    # Renderizar o template com os dados da vaga para edição
    vaga_data = {
        'id': vaga.id,
        'dados_pessoais': vaga.dados_pessoais,
        'dados_contato': vaga.dados_contato,
        'dados_profissionais': vaga.dados_profissionais,
        'dados_bancarios': vaga.dados_bancarios,
        'arquivos': vaga.arquivos
    }

    return render_template('editar_vaga.html', vaga=vaga_data, vaga_id=vaga_id)

@app.route('/vagas/excluir/<int:vaga_id>', methods=['POST'])
def excluir_vaga(vaga_id):
    try:
        vaga = Vaga.query.get_or_404(vaga_id)
        db.session.delete(vaga)
        db.session.commit()
        flash('Vaga excluída com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir vaga: {str(e)}', 'danger')
    return redirect(url_for('banco_vagas'))


@app.route('/vagas/importar', methods=['GET', 'POST'])
def importar_vagas():
    if request.method == 'POST':
        try:
            if 'arquivo' not in request.files:
                flash('Nenhum arquivo enviado', 'danger')
                return redirect(request.url)

            file = request.files['arquivo']
            if file.filename == '':
                flash('Nenhum arquivo selecionado', 'danger')
                return redirect(request.url)

            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)

                if filename.endswith('.csv'):
                    stream = StringIO(file.stream.read().decode("UTF8"), newline=None)
                    csv_reader = csv.DictReader(stream, delimiter=',')
                    vagas_data = [row for row in csv_reader]

                elif filename.endswith('.xlsx'):
                    df = pd.read_excel(file)
                    vagas_data = df.to_dict('records')

                else:
                    flash('Formato de arquivo não suportado', 'danger')
                    return redirect(request.url)

                count = 0
                for vaga_data in vagas_data:
                    try:
                        nova_vaga = Vaga(
                            dados_pessoais={
                                'nome_completo': vaga_data.get('nome_completo', ''),
                                'cpf': vaga_data.get('cpf', ''),
                                'data_nascimento': vaga_data.get('data_nascimento', ''),
                                'estado_civil': vaga_data.get('estado_civil', ''),
                                'dependentes': vaga_data.get('dependentes', '')
                            },
                            dados_contato={
                                'telefone': vaga_data.get('telefone', ''),
                                'email': vaga_data.get('email', ''),
                                'cep': vaga_data.get('cep', ''),
                                'cidade': vaga_data.get('cidade', ''),
                                'estado': vaga_data.get('estado', '')
                            },
                            dados_profissionais={
                                'area_atuacao': vaga_data.get('area_atuacao', ''),
                                'tipo_interesse': vaga_data.get('tipo_interesse', ''),
                                'disponibilidade': vaga_data.get('disponibilidade', ''),
                                'experiencia': vaga_data.get('experiencia', '')
                            },
                            dados_bancarios={
                                'banco': vaga_data.get('banco', ''),
                                'agencia': vaga_data.get('agencia', ''),
                                'conta': vaga_data.get('conta', ''),
                                'pix': vaga_data.get('pix', '')
                            },
                            arquivos={}
                        )
                        db.session.add(nova_vaga)
                        count += 1
                    except Exception as e:
                        db.session.rollback()
                        flash(f'Erro ao processar linha: {str(e)}', 'warning')
                        continue

                db.session.commit()
                flash(f'{count} vagas importadas com sucesso!', 'success')
                return redirect(url_for('banco_vagas'))

        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao importar vagas: {str(e)}', 'danger')
            app.logger.error(f"Erro na importação: {str(e)}", exc_info=True)

    return redirect(url_for('banco_vagas'))


@app.route('/vagas/download-modelo')
def download_modelo_vagas():
    output = StringIO()
    writer = csv.writer(output)

    writer.writerow([
        'nome_completo', 'cpf', 'data_nascimento', 'estado_civil', 'dependentes',
        'telefone', 'email', 'cep', 'cidade', 'estado',
        'area_atuacao', 'tipo_interesse', 'disponibilidade', 'experiencia',
        'banco', 'agencia', 'conta', 'pix'
    ])

    writer.writerow([
        'João Silva', '123.456.789-00', '1990-01-01', 'Solteiro', '0',
        '11999999999', 'joao@email.com', '01234-567', 'São Paulo', 'SP',
        'Promotor de Vendas', 'Temporário', 'Segunda a Sexta', '2 anos',
        'Banco do Brasil', '1234', '56789-0', '123.456.789-00'
    ])
    writer.writerow([
        'Maria Souza', '987.654.321-00', '1985-05-15', 'Casada', '2',
        '21988888888', 'maria@email.com', '21000-000', 'Rio de Janeiro', 'RJ',
        'Auxiliar Administrativo', 'Efetivo', 'Todos os dias', '5 anos',
        'Itaú', '4321', '12345-6', 'maria@email.com'
    ])

    output.seek(0)
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=modelo_vagas.csv"}
    )


# Rotas para Ações
@app.route('/acoes')
def banco_acoes():
    try:
        acoes = Acao.query.order_by(Acao.data_cadastro.desc()).all()

        for acao in acoes:
            if not isinstance(acao.status, str):
                acao.status = str(acao.status)

        return render_template('banco_acoes.html', acoes=acoes)
    except Exception as e:
        flash(f"Erro ao acessar banco de ações: {str(e)}", 'danger')
        return redirect(url_for('index'))


@app.route('/acoes/cadastrar', methods=['GET', 'POST'])
def cadastrar_acao():
    if request.method == 'POST':
        try:
            status_input = request.form.get('status', 'ativo').lower()
            if status_input not in [s.value for s in StatusAcao]:
                flash('Status inválido selecionado', 'danger')
                return render_template('cadastrar_acao.html')

            material_filename = handle_file_upload(request.files.get('material_acao'), 'material')
            foto_filename = handle_file_upload(request.files.get('foto_equipe'), 'foto')

            nova_acao = Acao(
                nome_cliente=request.form['nome_cliente'],
                empresa=request.form['empresa'],
                tipo_acao=request.form['tipo_acao'],
                quantidade_material=request.form['quantidade'],
                data_inicio=datetime.strptime(request.form['data_inicio'], '%Y-%m-%d').date(),
                data_termino=datetime.strptime(request.form['data_termino'], '%Y-%m-%d').date(),
                hora_inicio=request.form['hora_inicio'],
                hora_termino=request.form['hora_termino'],
                locais=request.form['locais'],
                quantidade_pessoas=request.form['quantidade_pessoas'],
                responsavel=request.form['responsavel'],
                status=status_input,
                material_acao=material_filename,
                foto_equipe=foto_filename
            )

            db.session.add(nova_acao)
            db.session.commit()
            flash('Ação cadastrada com sucesso!', 'success')
            return redirect(url_for('banco_acoes'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao cadastrar ação: {str(e)}', 'danger')
    return render_template('cadastrar_acao.html')


@app.route('/acoes/editar/<int:acao_id>', methods=['GET', 'POST'])
def editar_acao(acao_id):
    acao = Acao.query.get_or_404(acao_id)

    if request.method == 'POST':
        try:
            status_input = request.form.get('status', 'ativo').lower()
            if status_input not in [s.value for s in StatusAcao]:
                flash('Status inválido selecionado', 'danger')
                return redirect(url_for('editar_acao', acao_id=acao_id))

            acao.nome_cliente = request.form.get('nome_cliente', acao.nome_cliente)
            acao.empresa = request.form.get('empresa', acao.empresa)
            acao.tipo_acao = request.form.get('tipo_acao', acao.tipo_acao)
            acao.quantidade_material = request.form['quantidade']
            acao.status = status_input

            if request.form.get('data_inicio'):
                acao.data_inicio = datetime.strptime(request.form['data_inicio'], '%Y-%m-%d').date()
            if request.form.get('data_termino'):
                acao.data_termino = datetime.strptime(request.form['data_termino'], '%Y-%m-%d').date()

            acao.hora_inicio = request.form.get('hora_inicio', acao.hora_inicio)
            acao.hora_termino = request.form.get('hora_termino', acao.hora_termino)
            acao.locais = request.form.get('locais', acao.locais)
            acao.quantidade_pessoas = request.form.get('quantidade_pessoas', acao.quantidade_pessoas)
            acao.responsavel = request.form.get('responsavel', acao.responsavel)

            if 'material_acao' in request.files:
                material_file = request.files['material_acao']
                if material_file and allowed_file(material_file.filename):
                    filename = handle_file_upload(material_file, 'material')
                    if filename:
                        acao.material_acao = filename

            if 'foto_equipe' in request.files:
                foto_file = request.files['foto_equipe']
                if foto_file and allowed_file(foto_file.filename):
                    filename = handle_file_upload(foto_file, 'foto')
                    if filename:
                        acao.foto_equipe = filename

            db.session.commit()
            flash('Ação atualizada com sucesso!', 'success')
            return redirect(url_for('banco_acoes'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar ação: {str(e)}', 'danger')

    acao_data = {
        'id': acao.id,
        'nome_cliente': acao.nome_cliente,
        'empresa': acao.empresa,
        'tipo_acao': acao.tipo_acao,
        'quantidade': acao.quantidade_material,
        'data_inicio': acao.data_inicio.strftime('%Y-%m-%d') if acao.data_inicio else '',
        'data_termino': acao.data_termino.strftime('%Y-%m-%d') if acao.data_termino else '',
        'hora_inicio': acao.hora_inicio,
        'hora_termino': acao.hora_termino,
        'locais': acao.locais,
        'quantidade_pessoas': acao.quantidade_pessoas,
        'responsavel': acao.responsavel,
        'status': acao.status,
        'material_acao': acao.material_acao,
        'foto_equipe': acao.foto_equipe
    }

    return render_template('editar_acao.html', acao=acao_data, acao_id=acao_id)


@app.route('/acoes/excluir/<int:acao_id>', methods=['POST'])
def excluir_acao(acao_id):
    if request.method == 'POST':
        try:
            acao = Acao.query.get_or_404(acao_id)
            db.session.delete(acao)
            db.session.commit()
            flash('Ação excluída com sucesso!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao excluir ação: {str(e)}', 'danger')
    return redirect(url_for('banco_acoes'))


if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    with app.app_context():
        db.create_all()
    app.run(debug=True)

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime, timezone
from werkzeug.utils import secure_filename
import logging
from sqlalchemy.exc import SQLAlchemyError

app = Flask(__name__)
app.secret_key = 'ztX<Et-1Qw!2Ac5KIrfe87{4p}'

# Configuração do SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Configurações para upload de arquivos
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Vaga(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data_cadastro = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    # Dados Pessoais
    nome_completo = db.Column(db.String(100), nullable=False)
    data_nascimento = db.Column(db.String(20))
    estado_civil = db.Column(db.String(50))
    dependentes = db.Column(db.Integer)
    nacionalidade = db.Column(db.String(50))
    cpf = db.Column(db.String(20), unique=True)

    # Dados de Contato
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    cep = db.Column(db.String(10))
    cidade = db.Column(db.String(50))
    estado = db.Column(db.String(2))

    # Dados Profissionais
    area_atuacao = db.Column(db.String(100))
    tipo_interesse = db.Column(db.String(50))
    disponibilidade = db.Column(db.String(50))
    experiencia = db.Column(db.Text)

    # Dados Bancários
    banco = db.Column(db.String(50))
    agencia = db.Column(db.String(20))
    conta = db.Column(db.String(20))
    pix = db.Column(db.String(100))

    # Termos Legais
    lgpd = db.Column(db.Boolean, default=False)
    processos_seletivos = db.Column(db.Boolean, default=False)

    # Arquivos
    foto = db.Column(db.String(100))
    rg = db.Column(db.String(100))
    cpf_doc = db.Column(db.String(100))
    titulo_eleitor = db.Column(db.String(100))
    ctps = db.Column(db.String(100))
    certificacoes = db.Column(db.String(100))

class Acao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(50))
    descricao = db.Column(db.Text)
    data_inicio = db.Column(db.String(20))
    data_fim = db.Column(db.String(20))
    responsavel = db.Column(db.String(100))
    local = db.Column(db.String(100))
    data_cadastro = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

class Material(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(50))
    quantidade = db.Column(db.Integer)
    data_inicio = db.Column(db.String(20))
    data_termino = db.Column(db.String(20))
    locais = db.Column(db.String(200))
    quantidade_pessoas = db.Column(db.Integer)
    responsavel = db.Column(db.String(100))
    nome_cliente = db.Column(db.String(100))
    empresa = db.Column(db.String(100))
    data_cadastro = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    empresa = db.Column(db.String(100))
    segmento = db.Column(db.String(100))
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    cpf_cnpj = db.Column(db.String(20))
    data_cadastro = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('homepage.html')

@app.route('/cadastrar-material', methods=['GET', 'POST'])
def cadastrar_material():
    if request.method == 'POST':
        try:
            arquivos = {}
            for field in ['documento']:
                if field in request.files:
                    file = request.files[field]
                    if file and allowed_file(file.filename):
                        filename = secure_filename(f"{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{file.filename}")
                        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                        arquivos[field] = filename

            novo_material = Material(
                nome=request.form.get('campanha', ''),
                tipo=request.form.get('tipo_acao', ''),
                quantidade=int(request.form.get('quantidade', 0)),
                data_inicio=request.form.get('validade_inicio', ''),
                data_termino=request.form.get('validade_fim', ''),
                locais=request.form.get('locais', ''),
                quantidade_pessoas=int(request.form.get('quantidade_pessoas', 0)),
                responsavel=request.form.get('encarregado', ''),
                nome_cliente=request.form.get('nome_cliente', ''),
                empresa=request.form.get('empresa', '')
            )
            db.session.add(novo_material)
            db.session.commit()
            flash('Material cadastrado com sucesso!', 'success')
            return redirect(url_for('banco_materiais'))
        except ValueError as e:
            db.session.rollback()
            flash('Dados inválidos fornecidos', 'danger')
            logger.warning(f"Erro de validação ao cadastrar material: {str(e)}")
        except SQLAlchemyError as e:
            db.session.rollback()
            flash('Erro ao salvar no banco de dados', 'danger')
            logger.error(f"Erro de banco de dados ao cadastrar material: {str(e)}")
        except Exception as e:
            db.session.rollback()
            flash('Erro inesperado ao cadastrar material', 'danger')
            logger.error(f"Erro inesperado ao cadastrar material: {str(e)}", exc_info=True)
    return render_template('cadastrar_material.html')

@app.route('/cadastrar-cliente', methods=['GET', 'POST'])
def cadastrar_cliente():
    if request.method == 'POST':
        try:
            novo_cliente = Cliente(
                nome=request.form.get('nome_cliente', ''),
                empresa=request.form.get('empresa', ''),
                segmento=request.form.get('segmento', ''),
                telefone=request.form.get('telefone', ''),
                email=request.form.get('email', ''),
                cpf_cnpj=request.form.get('cpf_cnpj', '')
            )
            db.session.add(novo_cliente)
            db.session.commit()
            flash('Cliente cadastrado com sucesso!', 'success')
            return redirect(url_for('banco_clientes'))
        except ValueError as e:
            db.session.rollback()
            flash('Dados inválidos fornecidos', 'danger')
            logger.warning(f"Erro de validação ao cadastrar cliente: {str(e)}")
        except SQLAlchemyError as e:
            db.session.rollback()
            flash('Erro ao salvar no banco de dados', 'danger')
            logger.error(f"Erro de banco de dados ao cadastrar cliente: {str(e)}")
        except Exception as e:
            db.session.rollback()
            flash('Erro inesperado ao cadastrar cliente', 'danger')
            logger.error(f"Erro inesperado ao cadastrar cliente: {str(e)}", exc_info=True)
    return render_template('cadastrar_cliente.html')

@app.route('/cadastrar-acao', methods=['GET', 'POST'])
def cadastrar_acao():
    if request.method == 'POST':
        try:
            arquivos = {}
            for field in ['material_acao', 'foto_equipe']:
                if field in request.files:
                    file = request.files[field]
                    if file and allowed_file(file.filename):
                        filename = secure_filename(f"{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{file.filename}")
                        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                        arquivos[field] = filename

            nova_acao = Acao(
                nome=request.form.get('nome_cliente', '') + ' - ' + request.form.get('tipo_acao', ''),
                tipo=request.form.get('tipo_acao', ''),
                descricao=f"Cliente: {request.form.get('nome_cliente', '')}\nEmpresa: {request.form.get('empresa', '')}",
                data_inicio=request.form.get('data_inicio', ''),
                data_fim=request.form.get('data_termino', ''),
                responsavel=request.form.get('responsavel', ''),
                local=request.form.get('locais', '')
            )
            db.session.add(nova_acao)
            db.session.commit()
            flash('Ação cadastrada com sucesso!', 'success')
            return redirect(url_for('banco_acoes'))
        except ValueError as e:
            db.session.rollback()
            flash('Dados inválidos fornecidos', 'danger')
            logger.warning(f"Erro de validação ao cadastrar ação: {str(e)}")
        except SQLAlchemyError as e:
            db.session.rollback()
            flash('Erro ao salvar no banco de dados', 'danger')
            logger.error(f"Erro de banco de dados ao cadastrar ação: {str(e)}")
        except Exception as e:
            db.session.rollback()
            flash('Erro inesperado ao cadastrar ação', 'danger')
            logger.error(f"Erro inesperado ao cadastrar ação: {str(e)}", exc_info=True)
    return render_template('cadastrar_acao.html')

@app.route('/cadastrar-vaga', methods=['GET', 'POST'])
def cadastrar_vaga():
    if request.method == 'POST':
        try:
            arquivos = {}
            for field in ['foto', 'rg', 'cpf_doc', 'titulo_eleitor', 'ctps', 'certificacoes']:
                if field in request.files:
                    file = request.files[field]
                    if file and allowed_file(file.filename):
                        filename = secure_filename(f"{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{file.filename}")
                        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                        arquivos[field] = filename

            nova_vaga = Vaga(
                nome_completo=request.form.get('nome_completo', ''),
                data_nascimento=request.form.get('data_nascimento', ''),
                estado_civil=request.form.get('estado_civil', ''),
                dependentes=int(request.form.get('dependentes', 0)),
                nacionalidade=request.form.get('nacionalidade', ''),
                cpf=request.form.get('cpf', ''),
                telefone=request.form.get('telefone', ''),
                email=request.form.get('email', ''),
                cep=request.form.get('cep', ''),
                cidade=request.form.get('cidade', ''),
                estado=request.form.get('estado', ''),
                area_atuacao=request.form.get('area_atuacao', ''),
                tipo_interesse=request.form.get('tipo_interesse', ''),
                disponibilidade=request.form.get('disponibilidade', ''),
                experiencia=request.form.get('experiencia', ''),
                banco=request.form.get('banco', ''),
                agencia=request.form.get('agencia', ''),
                conta=request.form.get('conta', ''),
                pix=request.form.get('pix', ''),
                lgpd=request.form.get('lgpd') == 'on',
                processos_seletivos=request.form.get('processos_seletivos') == 'on',
                foto=arquivos.get('foto'),
                rg=arquivos.get('rg'),
                cpf_doc=arquivos.get('cpf_doc'),
                titulo_eleitor=arquivos.get('titulo_eleitor'),
                ctps=arquivos.get('ctps'),
                certificacoes=arquivos.get('certificacoes')
            )
            db.session.add(nova_vaga)
            db.session.commit()
            flash('Cadastro de vaga realizado com sucesso!', 'success')
            return redirect(url_for('banco_vagas'))
        except ValueError as e:
            db.session.rollback()
            flash('Dados inválidos fornecidos', 'danger')
            logger.warning(f"Erro de validação ao cadastrar vaga: {str(e)}")
        except SQLAlchemyError as e:
            db.session.rollback()
            flash('Erro ao salvar no banco de dados', 'danger')
            logger.error(f"Erro de banco de dados ao cadastrar vaga: {str(e)}")
        except Exception as e:
            db.session.rollback()
            flash('Erro inesperado ao cadastrar vaga', 'danger')
            logger.error(f"Erro inesperado ao cadastrar vaga: {str(e)}", exc_info=True)
    return render_template('cadastrar_vaga.html')

@app.route('/banco-clientes')
def banco_clientes():
    try:
        clientes = Cliente.query.order_by(Cliente.data_cadastro.desc()).all()
        return render_template('banco_clientes.html', clientes=clientes)
    except SQLAlchemyError as e:
        logger.error(f"Erro ao acessar banco de clientes: {str(e)}")
        flash('Erro ao acessar banco de clientes', 'danger')
        return redirect(url_for('index'))

@app.route('/banco-materiais')
def banco_materiais():
    try:
        materiais = Material.query.order_by(Material.data_cadastro.desc()).all()
        return render_template('banco_materiais.html', materiais=materiais)
    except SQLAlchemyError as e:
        logger.error(f"Erro ao acessar banco de materiais: {str(e)}")
        flash('Erro ao acessar banco de materiais', 'danger')
        return redirect(url_for('index'))

@app.route('/banco-vagas')
def banco_vagas():
    try:
        vagas = Vaga.query.order_by(Vaga.data_cadastro.desc()).all()
        return render_template('banco_vagas.html', vagas=vagas)
    except SQLAlchemyError as e:
        logger.error(f"Erro ao acessar banco de vagas: {str(e)}")
        flash('Erro ao acessar banco de vagas', 'danger')
        return redirect(url_for('index'))

@app.route('/banco-acoes')
def banco_acoes():
    try:
        acoes = Acao.query.order_by(Acao.data_cadastro.desc()).all()
        return render_template('banco_acoes.html', acoes=acoes)
    except SQLAlchemyError as e:
        logger.error(f"Erro ao acessar banco de ações: {str(e)}")
        flash('Erro ao acessar banco de ações', 'danger')
        return redirect(url_for('index'))

@app.route('/vaga/<int:vaga_id>')
def detalhes_vaga(vaga_id):
    try:
        vaga = Vaga.query.get_or_404(vaga_id)
        return render_template('detalhes_vaga.html', vaga=vaga)
    except SQLAlchemyError as e:
        logger.error(f"Erro ao buscar vaga {vaga_id}: {str(e)}")
        flash('Erro ao buscar informações da vaga', 'danger')
        return redirect(url_for('banco_vagas'))

@app.route('/acao/<int:acao_id>')
def detalhes_acao(acao_id):
    try:
        acao = Acao.query.get_or_404(acao_id)
        return render_template('detalhes_acao.html', acao=acao)
    except SQLAlchemyError as e:
        logger.error(f"Erro ao buscar ação {acao_id}: {str(e)}")
        flash('Erro ao buscar informações da ação', 'danger')
        return redirect(url_for('banco_acoes'))

@app.route('/material/<int:material_id>')
def detalhes_material(material_id):
    try:
        material = Material.query.get_or_404(material_id)
        return render_template('detalhes_material.html', material=material)
    except SQLAlchemyError as e:
        logger.error(f"Erro ao buscar material {material_id}: {str(e)}")
        flash('Erro ao buscar informações do material', 'danger')
        return redirect(url_for('banco_materiais'))

@app.route('/cliente/<int:cliente_id>')
def detalhes_cliente(cliente_id):
    try:
        cliente = Cliente.query.get_or_404(cliente_id)
        return render_template('detalhes_cliente.html', cliente=cliente)
    except SQLAlchemyError as e:
        logger.error(f"Erro ao buscar cliente {cliente_id}: {str(e)}")
        flash('Erro ao buscar informações do cliente', 'danger')
        return redirect(url_for('banco_clientes'))

@app.route('/editar-acao/<int:acao_id>', methods=['GET', 'POST'])
def editar_acao(acao_id):
    try:
        acao = Acao.query.get_or_404(acao_id)
        if request.method == 'POST':
            try:
                acao.nome = request.form.get('nome', acao.nome)
                acao.tipo = request.form.get('tipo', acao.tipo)
                acao.descricao = request.form.get('descricao', acao.descricao)
                acao.data_inicio = request.form.get('data_inicio', acao.data_inicio)
                acao.data_fim = request.form.get('data_fim', acao.data_fim)
                acao.responsavel = request.form.get('responsavel', acao.responsavel)
                acao.local = request.form.get('local', acao.local)
                db.session.commit()
                flash('Ação atualizada com sucesso!', 'success')
                return redirect(url_for('detalhes_acao', acao_id=acao.id))
            except ValueError as e:
                db.session.rollback()
                flash('Dados inválidos fornecidos', 'danger')
                logger.warning(f"Erro de validação ao editar ação {acao_id}: {str(e)}")
            except SQLAlchemyError as e:
                db.session.rollback()
                flash('Erro ao salvar alterações', 'danger')
                logger.error(f"Erro de banco de dados ao editar ação {acao_id}: {str(e)}")
            except Exception as e:
                db.session.rollback()
                flash('Erro inesperado ao editar ação', 'danger')
                logger.error(f"Erro inesperado ao editar ação {acao_id}: {str(e)}", exc_info=True)
        return render_template('editar_acao.html', acao=acao)
    except SQLAlchemyError as e:
        logger.error(f"Erro ao buscar ação para edição {acao_id}: {str(e)}")
        flash('Ação não encontrada', 'danger')
        return redirect(url_for('banco_acoes'))

@app.route('/editar-material/<int:material_id>', methods=['GET', 'POST'])
def editar_material(material_id):
    try:
        material = Material.query.get_or_404(material_id)
        if request.method == 'POST':
            try:
                material.nome = request.form.get('campanha', material.nome)
                material.tipo = request.form.get('tipo_acao', material.tipo)
                material.quantidade = int(request.form.get('quantidade', material.quantidade))
                material.data_inicio = request.form.get('validade_inicio', material.data_inicio)
                material.data_termino = request.form.get('validade_fim', material.data_termino)
                material.locais = request.form.get('locais', material.locais)
                material.quantidade_pessoas = int(request.form.get('quantidade_pessoas', material.quantidade_pessoas))
                material.responsavel = request.form.get('encarregado', material.responsavel)
                material.nome_cliente = request.form.get('nome_cliente', material.nome_cliente)
                material.empresa = request.form.get('empresa', material.empresa)
                db.session.commit()
                flash('Material atualizado com sucesso!', 'success')
                return redirect(url_for('detalhes_material', material_id=material.id))
            except ValueError as e:
                db.session.rollback()
                flash('Dados inválidos fornecidos', 'danger')
                logger.warning(f"Erro de validação ao editar material {material_id}: {str(e)}")
            except SQLAlchemyError as e:
                db.session.rollback()
                flash('Erro ao salvar alterações', 'danger')
                logger.error(f"Erro de banco de dados ao editar material {material_id}: {str(e)}")
            except Exception as e:
                db.session.rollback()
                flash('Erro inesperado ao editar material', 'danger')
                logger.error(f"Erro inesperado ao editar material {material_id}: {str(e)}", exc_info=True)
        return render_template('editar_material.html', material=material)
    except SQLAlchemyError as e:
        logger.error(f"Erro ao buscar material para edição {material_id}: {str(e)}")
        flash('Material não encontrado', 'danger')
        return redirect(url_for('banco_materiais'))

@app.route('/editar-cliente/<int:cliente_id>', methods=['GET', 'POST'])
def editar_cliente(cliente_id):
    try:
        cliente = Cliente.query.get_or_404(cliente_id)
        if request.method == 'POST':
            try:
                cliente.nome = request.form.get('nome_cliente', cliente.nome)
                cliente.empresa = request.form.get('empresa', cliente.empresa)
                cliente.segmento = request.form.get('segmento', cliente.segmento)
                cliente.telefone = request.form.get('telefone', cliente.telefone)
                cliente.email = request.form.get('email', cliente.email)
                cliente.cpf_cnpj = request.form.get('cpf_cnpj', cliente.cpf_cnpj)
                db.session.commit()
                flash('Cliente atualizado com sucesso!', 'success')
                return redirect(url_for('detalhes_cliente', cliente_id=cliente.id))
            except ValueError as e:
                db.session.rollback()
                flash('Dados inválidos fornecidos', 'danger')
                logger.warning(f"Erro de validação ao editar cliente {cliente_id}: {str(e)}")
            except SQLAlchemyError as e:
                db.session.rollback()
                flash('Erro ao salvar alterações', 'danger')
                logger.error(f"Erro de banco de dados ao editar cliente {cliente_id}: {str(e)}")
            except Exception as e:
                db.session.rollback()
                flash('Erro inesperado ao editar cliente', 'danger')
                logger.error(f"Erro inesperado ao editar cliente {cliente_id}: {str(e)}", exc_info=True)
        return render_template('editar_cliente.html', cliente=cliente)
    except SQLAlchemyError as e:
        logger.error(f"Erro ao buscar cliente para edição {cliente_id}: {str(e)}")
        flash('Cliente não encontrado', 'danger')
        return redirect(url_for('banco_clientes'))

@app.route('/excluir-acao/<int:acao_id>', methods=['POST'])
def excluir_acao(acao_id):
    try:
        acao = Acao.query.get_or_404(acao_id)
        nome_acao = acao.nome
        db.session.delete(acao)
        db.session.commit()
        flash(f'Ação "{nome_acao}" excluída com sucesso!', 'success')
    except SQLAlchemyError as e:
        db.session.rollback()
        flash('Erro ao excluir ação', 'danger')
        logger.error(f"Erro ao excluir ação {acao_id}: {str(e)}")
    except Exception as e:
        db.session.rollback()
        flash('Erro inesperado ao excluir ação', 'danger')
        logger.error(f"Erro inesperado ao excluir ação {acao_id}: {str(e)}", exc_info=True)
    return redirect(url_for('banco_acoes'))

@app.route('/excluir-material/<int:material_id>', methods=['POST'])
def excluir_material(material_id):
    try:
        material = Material.query.get_or_404(material_id)
        nome_material = material.nome
        db.session.delete(material)
        db.session.commit()
        flash(f'Material "{nome_material}" excluído com sucesso!', 'success')
    except SQLAlchemyError as e:
        db.session.rollback()
        flash('Erro ao excluir material', 'danger')
        logger.error(f"Erro ao excluir material {material_id}: {str(e)}")
    except Exception as e:
        db.session.rollback()
        flash('Erro inesperado ao excluir material', 'danger')
        logger.error(f"Erro inesperado ao excluir material {material_id}: {str(e)}", exc_info=True)
    return redirect(url_for('banco_materiais'))

@app.route('/excluir-cliente/<int:cliente_id>', methods=['POST'])
def excluir_cliente(cliente_id):
    try:
        cliente = Cliente.query.get_or_404(cliente_id)
        nome_cliente = cliente.nome
        db.session.delete(cliente)
        db.session.commit()
        flash(f'Cliente "{nome_cliente}" excluído com sucesso!', 'success')
    except SQLAlchemyError as e:
        db.session.rollback()
        flash('Erro ao excluir cliente', 'danger')
        logger.error(f"Erro ao excluir cliente {cliente_id}: {str(e)}")
    except Exception as e:
        db.session.rollback()
        flash('Erro inesperado ao excluir cliente', 'danger')
        logger.error(f"Erro inesperado ao excluir cliente {cliente_id}: {str(e)}", exc_info=True)
    return redirect(url_for('banco_clientes'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)
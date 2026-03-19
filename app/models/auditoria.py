from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime

from app.extensions import db
from app.models.auditoria import Auditoria  # ✅ CORRIGIDO AQUI
from app.models.acao_promocional import AcaoPromocional
from app.models.turno import Turno
from app.services.cloudinary_service import CloudinaryService

auditorias_bp = Blueprint('auditorias', __name__, url_prefix='/auditorias')


# =============================
# LISTAR AUDITORIAS
# =============================
@auditorias_bp.route('/')
@login_required
def listar():
    auditorias = Auditoria.query.order_by(Auditoria.data_hora.desc()).all()
    return render_template('auditorias/listar.html', auditorias=auditorias)


# =============================
# REGISTRAR AUDITORIA
# =============================
@auditorias_bp.route('/registrar', methods=['GET', 'POST'])
@login_required
def registrar():

    if request.method == 'GET':
        acoes = AcaoPromocional.query.all()

        # 🔥 MOSTRAR APENAS TURNOS ATIVOS
        turnos = Turno.query.filter_by(status='ativo').all()

        return render_template(
            'auditorias/registrar.html',
            acoes=acoes,
            turnos=turnos
        )

    # =============================
    # POST
    # =============================
    acao_id = request.form.get('acao_id', type=int)
    turno_id = request.form.get('turno_id', type=int)

    descricao = request.form.get('descricao')
    latitude = request.form.get('latitude', type=float)
    longitude = request.form.get('longitude', type=float)
    foto = request.files.get('foto')

    # 🔥 VALIDAÇÃO CORRETA (evita erro com 0.0)
    if not acao_id or latitude is None or longitude is None or not foto:
        flash('Preencha todos os campos obrigatórios.', 'danger')
        return redirect(request.url)

    # =============================
    # 🔥 LÓGICA DE TURNO
    # =============================
    turno = None

    # 1. Se veio turno_id (PRIORIDADE)
    if turno_id:
        turno = Turno.query.get(turno_id)

    # 2. Fallback automático
    elif acao_id:
        turno = Turno.query.filter_by(
            acao_id=acao_id,
            status='ativo'
        ).order_by(Turno.inicio.desc()).first()

        # 🔥 Criação automática se não existir
        if not turno:
            try:
                turno = Turno(
                    acao_id=acao_id,
                    equipe_id=getattr(current_user, 'equipe_id', None),
                    inicio=datetime.utcnow(),
                    status='ativo'
                )
                db.session.add(turno)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                flash(f'Erro ao criar turno automático: {str(e)}', 'danger')
                return redirect(request.url)

    # 3. Falha definitiva
    if not turno:
        flash('Nenhum turno disponível. Inicie um turno.', 'danger')
        return redirect(request.url)

    # =============================
    # UPLOAD DA FOTO
    # =============================
    try:
        foto_url = CloudinaryService.upload_image(foto, folder="auditorias")
    except Exception as e:
        flash(f'Erro ao enviar imagem: {str(e)}', 'danger')
        return redirect(request.url)

    # =============================
    # SALVAR AUDITORIA
    # =============================
    try:
        nova_auditoria = Auditoria(
            turno_id=turno.id,
            acao_id=acao_id,
            user_id=current_user.id,
            descricao=descricao,
            foto_url=foto_url,
            latitude=latitude,
            longitude=longitude,
            data_hora=datetime.utcnow()
        )

        db.session.add(nova_auditoria)
        db.session.commit()

        flash('Auditoria registrada com sucesso!', 'success')
        return redirect(url_for('auditorias.listar'))

    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao salvar auditoria: {str(e)}', 'danger')
        return redirect(request.url)

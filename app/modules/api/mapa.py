from flask import Blueprint, jsonify, request
from flask_login import login_required
from app.models.auditoria import Auditoria
from app.extensions import db
from datetime import datetime
import json

bp = Blueprint('api_mapa', __name__)

@bp.route('/api/mapa/fotos')
@login_required
def fotos_mapa():
    # Buscar todas as auditorias ordenadas por data
    auditorias = Auditoria.query.order_by(Auditoria.data_hora.desc()).all()
    resultado = []
    
    for a in auditorias:
        if not a.latitude or not a.longitude:
            continue
            
        # Buscar o período do turno (Manhã, Tarde, etc.) da Ação vinculada
        periodo_turno = a.acao.turno if a.acao else "N/A"
        
        resultado.append({
            "lat": a.latitude,
            "lng": a.longitude,
            "img": a.foto_url,
            "descricao": a.descricao,
            "data": a.data_hora.isoformat() if a.data_hora else None,
            "id": a.id,
            "turno_id": periodo_turno
        })
    return jsonify(resultado)

@bp.route('/api/mapa/areas')
@login_required
def areas_mapa():
    from app.models.area_atuacao import AreaAtuacao
    # Buscar todas as áreas de atuação cadastradas
    areas = AreaAtuacao.query.all()
    
    resultado = []
    for area in areas:
        geojson = area.get_geojson()
        if geojson:
            resultado.append({
                "id": area.id,
                "nome": area.nome,
                "descricao": area.descricao,
                "geojson": geojson,
                "cor": area.cor or "#0d6efd",
                "acao_id": area.acao_id
            })
            
    return jsonify(resultado)

@bp.route('/api/mapa/areas/salvar', methods=['POST'])
@login_required
def salvar_area():
    from app.models.area_atuacao import AreaAtuacao
    
    data = request.get_json()
    
    if not data or not data.get('acao_id') or not data.get('geojson'):
        return jsonify({"erro": "Dados insuficientes para salvar a área"}), 400
    
    try:
        # Criar novo registro de área no banco de dados
        nova_area = AreaAtuacao(
            acao_id=data.get('acao_id'),
            nome=data.get('nome', f"Área {datetime.now().strftime('%H:%M')}"),
            descricao=data.get('descricao', 'Área delimitada via mapa'),
            geojson=json.dumps(data.get('geojson')),
            cor=data.get('cor', '#0d6efd')
        )
        
        db.session.add(nova_area)
        db.session.commit()
        
        return jsonify({
            "sucesso": True, 
            "id": nova_area.id,
            "mensagem": "Área salva com sucesso!"
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"erro": f"Erro ao salvar no banco: {str(e)}"}), 500

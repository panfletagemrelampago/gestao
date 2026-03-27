from datetime import datetime, timezone, timedelta
from app.extensions import db
from app.models.turno import Turno
from app.models.acao_promocional import AcaoPromocional
from app.models.veiculo import Veiculo
from app.models.equipe import Equipe
import json

class TurnoService:
    @staticmethod
    def get_local_now():
        """Retorna datetime atual no fuso de Cuiabá (GMT-4)"""
        return datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=-4))).replace(tzinfo=None)

    @staticmethod
    def iniciar_turno(acao_id, user):
        """
        Inicia um novo turno para uma ação.
        Regras:
        - Apenas funcionários podem iniciar.
        - Não pode haver outro turno 'em andamento' ou 'pausado' para a mesma ação.
        """
        if user.tipo_usuario != 'funcionario':
            raise ValueError("Apenas funcionários podem iniciar turnos.")

        acao = AcaoPromocional.query.get_or_404(acao_id)
        
        # Validação de estado: não permitir se já houver turno ativo ou pausado
        turno_ativo = Turno.query.filter(
            Turno.acao_id == acao_id,
            Turno.status.in_(['em andamento', 'pausado'])
        ).first()
        
        if turno_ativo:
            raise ValueError(f"Já existe um turno {turno_ativo.status} para esta ação.")

        # Busca de veículo (lógica robusta mantida)
        veiculo_vinculado = Veiculo.query.filter_by(motorista_id=acao.lider_equipe_id).first()
        if not veiculo_vinculado and acao.lider:
            nome_lider = acao.lider.nome.split()[0]
            veiculo_vinculado = Veiculo.query.filter(Veiculo.modelo.ilike(f"%{nome_lider}%")).first()
        if not veiculo_vinculado:
            veiculo_vinculado = Veiculo.query.filter_by(status=True).first()
            
        veiculo_id = veiculo_vinculado.id if veiculo_vinculado else None

        novo_turno = Turno(
            acao_id=acao_id,
            equipe_id=acao.lider_equipe_id,
            veiculo_id=veiculo_id,
            inicio=datetime.utcnow(),
            status='em andamento',
            pausas_json='[]'
        )
        
        # 🔥 Atualiza status da ação para 'Em Andamento'
        acao.status = 'Em Andamento'
        
        db.session.add(novo_turno)
        db.session.commit()
        return novo_turno

    @staticmethod
    def pausar_turno(turno_id, user):
        """
        Pausa um turno em andamento.
        Regras:
        - Apenas funcionários podem pausar.
        - Turno deve estar 'em andamento'.
        """
        if user.tipo_usuario != 'funcionario':
            raise ValueError("Apenas funcionários podem pausar turnos.")

        turno = Turno.query.get_or_404(turno_id)
        
        if turno.status != 'em andamento':
            raise ValueError(f"Não é possível pausar um turno com status '{turno.status}'.")

        pausas = turno.pausas
        pausas.append({
            'inicio': datetime.utcnow().isoformat(),
            'fim': None
        })
        turno.pausas = pausas
        turno.status = 'pausado'
        
        # 🔥 Sincronizar status da Ação para 'Pausada'
        acao = AcaoPromocional.query.get(turno.acao_id)
        if acao:
            acao.status = 'Pausada'
        
        db.session.commit()
        return turno

    @staticmethod
    def retomar_turno(turno_id, user):
        """
        Retoma um turno pausado.
        Regras:
        - Apenas funcionários podem retomar.
        - Turno deve estar 'pausado'.
        """
        if user.tipo_usuario != 'funcionario':
            raise ValueError("Apenas funcionários podem retomar turnos.")

        turno = Turno.query.get_or_404(turno_id)
        
        if turno.status != 'pausado':
            raise ValueError(f"Não é possível retomar um turno com status '{turno.status}'.")

        pausas = turno.pausas
        if pausas and pausas[-1]['fim'] is None:
            pausas[-1]['fim'] = datetime.utcnow().isoformat()
        
        turno.pausas = pausas
        turno.status = 'em andamento'
        
        # 🔥 Sincronizar status da Ação para 'Em Andamento'
        acao = AcaoPromocional.query.get(turno.acao_id)
        if acao:
            acao.status = 'Em Andamento'
        
        db.session.commit()
        return turno

    @staticmethod
    def encerrar_turno(turno_id, user, observacoes=None):
        """
        Encerra um turno.
        Regras:
        - Apenas funcionários podem encerrar.
        - Turno deve estar 'em andamento' ou 'pausado'.
        """
        if user.tipo_usuario != 'funcionario':
            raise ValueError("Apenas funcionários podem encerrar turnos.")

        turno = Turno.query.get_or_404(turno_id)
        
        if turno.status == 'finalizado':
            raise ValueError("Este turno já foi finalizado.")

        # Se estava pausado, fecha a última pausa
        if turno.status == 'pausado':
            pausas = turno.pausas
            if pausas and pausas[-1]['fim'] is None:
                pausas[-1]['fim'] = datetime.utcnow().isoformat()
            turno.pausas = pausas

        turno.status = 'finalizado'
        turno.fim = datetime.utcnow()
        if observacoes:
            turno.observacoes = observacoes
            
        # 🔥 Sincronizar status da Ação:
        # Se não houver mais nenhum turno 'em andamento' ou 'pausado' para esta ação,
        # mudamos o status da ação para 'Finalizada'.
        outros_turnos_ativos = Turno.query.filter(
            Turno.acao_id == turno.acao_id,
            Turno.id != turno.id,
            Turno.status.in_(['em andamento', 'pausado'])
        ).count()
        
        if outros_turnos_ativos == 0:
            acao = AcaoPromocional.query.get(turno.acao_id)
            if acao:
                acao.status = 'Finalizada'
            
        db.session.commit()
        return turno

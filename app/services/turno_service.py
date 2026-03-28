"""
TurnoService: camada de serviço para gerenciamento do ciclo de vida dos turnos.

REFATORAÇÃO (Passos 1 e 3):
- Toda persistência de datetime usa _utcnow() (UTC naive) — sem mistura de fusos.
- get_local_now() mantido APENAS para uso na camada de exibição (templates);
  não deve ser chamado em operações de escrita no banco.
- Heurística de busca do veículo do líder centralizada em
  Veiculo.buscar_para_lider(), eliminando duplicidade com auditorias/routes.py.
"""

from datetime import datetime, timezone, timedelta
from app.extensions import db
from app.models.turno import Turno
from app.models.acao_promocional import AcaoPromocional
from app.models.veiculo import Veiculo
from app.models.equipe import Equipe
import json


def _utcnow():
    """Retorna datetime UTC naive para persistência uniforme no PostgreSQL."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class TurnoService:

    @staticmethod
    def get_local_now():
        """
        Retorna datetime atual no fuso de Cuiabá (GMT-4).
        USO EXCLUSIVO na camada de exibição (templates, relatórios).
        NÃO utilizar para persistência no banco de dados.
        """
        return datetime.now(timezone.utc).astimezone(
            timezone(timedelta(hours=-4))
        ).replace(tzinfo=None)

    @staticmethod
    def to_local_tz(dt):
        """
        Converte um datetime UTC (naive ou aware) para GMT-4 naive.
        USO EXCLUSIVO na camada de exibição.
        """
        if dt is None:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone(timedelta(hours=-4))).replace(tzinfo=None)

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

        turno_ativo = Turno.query.filter(
            Turno.acao_id == acao_id,
            Turno.status.in_(['em andamento', 'pausado'])
        ).first()

        if turno_ativo:
            raise ValueError(f"Já existe um turno {turno_ativo.status} para esta ação.")

        # Heurística centralizada (Passo 3): delega ao método do modelo Veiculo
        veiculo_vinculado = Veiculo.buscar_para_lider(acao.lider_equipe_id, acao.lider)
        veiculo_id = veiculo_vinculado.id if veiculo_vinculado else None

        novo_turno = Turno(
            acao_id=acao_id,
            equipe_id=acao.lider_equipe_id,
            veiculo_id=veiculo_id,
            inicio=_utcnow(),
            status='em andamento',
            pausas_json='[]'
        )

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
            'inicio': _utcnow().isoformat(),
            'fim': None
        })
        turno.pausas = pausas
        turno.status = 'pausado'

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
            pausas[-1]['fim'] = _utcnow().isoformat()

        turno.pausas = pausas
        turno.status = 'em andamento'

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

        if turno.status == 'pausado':
            pausas = turno.pausas
            if pausas and pausas[-1]['fim'] is None:
                pausas[-1]['fim'] = _utcnow().isoformat()
            turno.pausas = pausas

        turno.status = 'finalizado'
        turno.fim = _utcnow()
        if observacoes:
            turno.observacoes = observacoes

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

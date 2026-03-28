"""
Model Veiculo.

REFATORAÇÃO (Passo 3 – Centralização de Heurísticas):
- Adicionado método de classe `buscar_para_lider(lider_equipe_id, lider)` que
  encapsula a heurística de três etapas de busca do veículo do líder da equipe.
  Essa lógica estava duplicada em TurnoService.iniciar_turno e em
  auditorias/routes.py (tela de turnos). Agora existe uma única fonte da verdade.
"""

from datetime import datetime, timezone
from app.extensions import db


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Veiculo(db.Model):
    __tablename__ = 'veiculos'

    id = db.Column(db.Integer, primary_key=True)
    marca = db.Column(db.String(50), nullable=False)
    modelo = db.Column(db.String(50), nullable=False)
    placa = db.Column(db.String(10), unique=True, nullable=False)
    cor = db.Column(db.String(20), nullable=False)
    motorista_id = db.Column(db.Integer, db.ForeignKey('equipes.id'), nullable=True)
    status = db.Column(db.Boolean, default=True)
    data_cadastro = db.Column(db.DateTime, default=_utcnow)

    @classmethod
    def buscar_para_lider(cls, lider_equipe_id, lider=None):
        """
        Heurística centralizada de três etapas para encontrar o veículo do líder:

        1. Busca direta por motorista_id == lider_equipe_id (vínculo explícito).
        2. Fallback: busca pelo primeiro nome do líder no campo modelo (ILIKE).
        3. Fallback final: qualquer veículo com status=True (ativo).

        Retorna a instância de Veiculo encontrada ou None se não houver nenhum.
        """
        if lider_equipe_id:
            veiculo = cls.query.filter_by(motorista_id=lider_equipe_id).first()
            if veiculo:
                return veiculo

        if lider and lider.nome:
            primeiro_nome = lider.nome.split()[0]
            veiculo = cls.query.filter(
                cls.modelo.ilike(f"%{primeiro_nome}%")
            ).first()
            if veiculo:
                return veiculo

        return cls.query.filter_by(status=True).first()

    def __repr__(self):
        return f'<Veiculo {self.placa}>'

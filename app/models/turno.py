"""
Model Turno: representa um período de trabalho de campo vinculado a uma ação
promocional, equipe e veículo. Registra início, fim, pausas e status do turno.
"""
from datetime import datetime, timezone, timedelta
from app.extensions import db
import json

class Turno(db.Model):
    __tablename__ = 'turnos'

    id = db.Column(db.Integer, primary_key=True)
    acao_id = db.Column(
        db.Integer,
        db.ForeignKey('acoes_promocionais.id'),
        nullable=False,
        index=True
    )
    equipe_id = db.Column(
        db.Integer,
        db.ForeignKey('equipes.id'),
        nullable=True,
        index=True
    )
    veiculo_id = db.Column(
        db.Integer,
        db.ForeignKey('veiculos.id'),
        nullable=True
    )
    inicio = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    fim = db.Column(db.DateTime, nullable=True)
    
    # Status: 'não iniciado', 'em andamento', 'pausado', 'finalizado'
    status = db.Column(
        db.String(20),
        nullable=False,
        default='em andamento'
    )
    
    # Armazena pausas como JSON: [{"inicio": "...", "fim": "..."}]
    pausas_json = db.Column(db.Text, nullable=True, default='[]')
    
    observacoes = db.Column(db.Text, nullable=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacionamentos
    acao = db.relationship('AcaoPromocional', backref='turnos', lazy=True)
    equipe = db.relationship('Equipe', backref='turnos', lazy=True)
    veiculo = db.relationship('Veiculo', backref='turnos', lazy=True)
    fotos = db.relationship('FotoAuditoria', backref='turno', lazy=True, cascade='all, delete-orphan')

    @property
    def pausas(self):
        try:
            return json.loads(self.pausas_json or '[]')
        except:
            return []

    @pausas.setter
    def pausas(self, value):
        self.pausas_json = json.dumps(value)

    @property
    def duracao_total_segundos(self):
        """Calcula a duração líquida do turno (excluindo pausas) em segundos."""
        if not self.inicio:
            return 0
        
        # Garantir que o início seja naive para comparação (banco salva como naive UTC)
        inicio_naive = self.inicio.replace(tzinfo=None) if self.inicio.tzinfo else self.inicio
        
        # Fim de referência (agora ou fim do turno)
        if self.fim:
            fim_referencia = self.fim.replace(tzinfo=None) if self.fim.tzinfo else self.fim
        else:
            fim_referencia = datetime.utcnow()
            
        total_bruto = (fim_referencia - inicio_naive).total_seconds()
        
        total_pausas = 0
        pausas = self.pausas
        for p in pausas:
            try:
                p_inicio = datetime.fromisoformat(p['inicio']).replace(tzinfo=None)
                if p.get('fim'):
                    p_fim = datetime.fromisoformat(p['fim']).replace(tzinfo=None)
                else:
                    p_fim = fim_referencia
                
                if p_fim > p_inicio:
                    total_pausas += (p_fim - p_inicio).total_seconds()
            except (ValueError, TypeError):
                continue
            
        duracao = total_bruto - total_pausas
        return max(0, int(duracao))

    @property
    def duracao_minutos(self):
        """Retorna a duração líquida em minutos."""
        return int(self.duracao_total_segundos / 60)

    def __repr__(self):
        return f'<Turno {self.id} - Acao {self.acao_id} - {self.status}>'

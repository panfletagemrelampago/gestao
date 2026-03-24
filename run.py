import os
from app import create_app, db
from app.models.user import User
from app.models.cliente import Cliente
from app.models.equipe import Equipe
from app.models.veiculo import Veiculo
from app.models.acao_promocional import AcaoPromocional
from app.models.auditoria import Auditoria
from app.models.posicao_gps import PosicaoGps
from app.models.turno import Turno
from app.models.area_atuacao import AreaAtuacao
from app.models.foto_auditoria import FotoAuditoria

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'User': User,
        'Cliente': Cliente,
        'Equipe': Equipe,
        'Veiculo': Veiculo,
        'AcaoPromocional': AcaoPromocional,
        'Auditoria': Auditoria,
        'PosicaoGps': PosicaoGps,
        'Turno': Turno,
        'AreaAtuacao': AreaAtuacao,
        'FotoAuditoria': FotoAuditoria
    }

if __name__ == '__main__':
    instance_path = os.path.join(os.path.dirname(__file__), 'instance')
    if not os.path.exists(instance_path):
        os.makedirs(instance_path)



    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

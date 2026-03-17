======================================================================
           SISTEMA DE GESTAO PROMOCIONAL E AUDITORIA
======================================================================

Sistema web profissional para auditoria de marketing promocional e 
panfletagem, com rastreamento GPS em tempo real e prova de cobertura 
geolocalizada atraves de uma infraestrutura propria de monitoramento.

----------------------------------------------------------------------
1. FUNCIONALIDADES PRINCIPAIS
----------------------------------------------------------------------

- Rastreamento GPS Proprio: Monitoramento continuo das equipes em 
  campo via API interna de geolocalizacao.
- Auditoria Geolocalizada: Registro de fotos de evidencia com 
  coordenadas GPS capturadas no momento da acao e upload para Cloudinary.
- Mapa Interativo: Visualizacao em tempo real de rastros, usuarios 
  ativos e areas de atuacao usando Leaflet.js.
- Gestao de Campanhas: Controle completo de acoes promocionais, 
  clientes, equipes, veiculos e turnos.
- Filtro de Precisao: Logica de filtragem de coordenadas para garantir 
  rastros limpos e precisos no mapa.

----------------------------------------------------------------------
2. TECNOLOGIAS UTILIZADAS
----------------------------------------------------------------------

- Backend: Python 3.11+ com Flask
- Banco de Dados: SQLAlchemy (SQLite/PostgreSQL)
- Frontend: Bootstrap 5, Leaflet.js, FontAwesome
- Servicos Externos: Cloudinary (Gestao de Imagens)

----------------------------------------------------------------------
3. INSTALACAO E EXECUCAO
----------------------------------------------------------------------

3.1. Clone o projeto e entre no diretorio:
     cd gestao_promocional

3.2. Crie um ambiente virtual e instale as dependencias:
     python -m venv .venv
     
     # Ativacao (Windows):
     .venv\Scripts\activate
     
     # Ativacao (Linux/macOS):
     source .venv/bin/activate
     
     pip install -r requirements.txt

3.3. Configure as variaveis de ambiente:
     - Copie o arquivo .env.example para .env
     - Preencha as chaves do Cloudinary e a SECRET_KEY do Flask.

3.4. Inicialize o banco de dados:
     O sistema cria as tabelas automaticamente ao iniciar (run.py).
     Para migracoes futuras, utilize:
     flask db upgrade

3.5. Execute a aplicacao:
     python run.py
     
     Acesse: http://localhost:10000 (ou a porta configurada)

----------------------------------------------------------------------
4. ESTRUTURA DO PROJETO
----------------------------------------------------------------------

- app/models/     : Tabelas do banco (User, PosicaoGps, Auditoria, etc.)
- app/modules/    : Blueprints com a logica de rotas e APIs.
- app/templates/  : Interface do mapa e dashboards.
- app/static/js/  : Scripts de rastreamento (gps_tracker.js).

----------------------------------------------------------------------
Desenvolvido por Relâmpago Distribuições
======================================================================
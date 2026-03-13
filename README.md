# Sistema de Gestão Promocional e Auditoria

Sistema web profissional para auditoria de marketing promocional e panfletagem, com rastreamento GPS em tempo real e prova de cobertura geolocalizada.

## Funcionalidades Principais

- **Rastreamento GPS**: Integração com a API do Traccar para monitoramento das equipes em campo.
- **Auditoria Geolocalizada**: Registro de fotos de evidência com coordenadas GPS e upload automático para Cloudinary.
- **Mapa Interativo**: Visualização em tempo real de rastros, veículos e auditorias usando Leaflet.js.
- **Gestão de Campanhas**: Controle completo de ações promocionais, clientes, equipes e veículos.
- **Multi-Nível de Acesso**: Interfaces customizadas para Administradores, Equipes de Campo e Clientes.

## Tecnologias Utilizadas

- **Backend**: Python 3.11+ com Flask
- **Banco de Dados**: SQLAlchemy (SQLite/PostgreSQL)
- **Frontend**: Bootstrap 5, Leaflet.js, FontAwesome
- **Serviços Externos**: Traccar API (GPS), Cloudinary (Imagens)

## Instalação e Execução

1.  **Clone o projeto e entre no diretório**:
    ```bash
    cd gestao_promocional
    ```

2.  **Crie um ambiente virtual e instale as dependências**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # Linux/macOS
    # ou
    venv\Scripts\activate  # Windows
    pip install -r requirements.txt
    ```

3.  **Configure as variáveis de ambiente**:
    - Copie o arquivo `.env.example` para `.env`.
    - Preencha as chaves do Cloudinary e as credenciais do servidor Traccar.

4.  **Inicialize o banco de dados**:
    ```bash
    flask db init
    flask db migrate -m "Initial migration"
    flask db upgrade
    ```

5.  **Crie um usuário administrador inicial**:
    Você pode usar o `flask shell` para criar o primeiro admin:
    ```python
    from app.models.user import User
    from app.extensions import db
    admin = User(nome_exibicao=\'Admin\', email=\'admin@agencia.com\', tipo_usuario=\'admin\')
    admin.set_password(\'suasenha\')
    db.session.add(admin)
    db.session.commit()
    ```

6.  **Execute a aplicação**:
    ```bash
    python run.py
    ```
    Acesse: `http://localhost:5000`

## Estrutura do Projeto

- `app/models/`: Definições das tabelas do banco de dados.
- `app/modules/`: Blueprints contendo a lógica das rotas por funcionalidade.
- `app/services/`: Camada de serviços para integrações (GPS, Imagens).
- `app/templates/`: Arquivos HTML organizados por módulo.
- `app/static/`: Arquivos CSS e JavaScript.

---
Desenvolvido por **Manus AI** - 2026

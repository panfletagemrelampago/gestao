# Planejamento do Módulo de Auditoria

## O que já existe
O projeto já possui uma estrutura básica funcional com Flask, SQLAlchemy e Blueprints.
Já existem os seguintes models relacionados à auditoria:
- `PosicaoGps`: Armazena posições (device_id, lat, lon, velocidade, bateria, data_hora).
- `Auditoria`: Armazena fotos com geolocalização (acao_id, user_id, descricao, foto_url, lat, lon, data_hora).
- `AcaoPromocional`: Representa a ação em si.
- `Veiculo`, `Equipe`, `Cliente`, `User`.

Existem endpoints básicos:
- `/api/gps/receber`: Recebe posições e salva no banco usando `GpsService`.
- `/api/mapa/dados`: Retorna dados de auditorias, veículos e rastros para o mapa.
- `mapa/index.html`: Exibe um mapa Leaflet básico com rastros (polyline) e marcadores de auditoria.

## O que falta (Lacunas)

### 1. Models
- **Turno**: O usuário pediu o model `Turno` com campos: `acao_id`, `equipe_id`, `veiculo_id`, `inicio`, `fim`, `status`. Isso não existe atualmente.
- **AreaAtuacao**: O usuário pediu o model `AreaAtuacao` com campos: `acao_id`, `nome`, `geojson`. Isso não existe.
- **FotoAuditoria**: O usuário pediu o model `FotoAuditoria` (auditoria_id, url, latitude, longitude, data_hora). O model atual `Auditoria` funciona de forma semelhante, mas precisamos ajustá-lo ou criar o novo model conforme solicitado. Vamos manter a compatibilidade ou criar `FotoAuditoria` ligado a `Auditoria` (ou renomear/adaptar). O pedido diz "Model FotoAuditoria: auditoria_id, url, latitude, longitude, data_hora". Atualmente, a tabela `auditorias` já tem foto. Talvez uma auditoria tenha várias fotos? Vou criar `FotoAuditoria` vinculado à tabela `auditorias` ou adaptar para que `Auditoria` seja o evento principal e `FotoAuditoria` sejam as fotos.

### 2. Endpoints e Rotas
- **Turnos**: API ou rotas para iniciar/finalizar turnos.
- **Áreas**: Endpoint para salvar e carregar GeoJSON das áreas de atuação de uma ação.
- **Relatório**: Rota para gerar e exibir o relatório da ação (mapa da rota, fotos, horário, equipe, cliente).

### 3. Mapa Leaflet (Frontend)
- **Desenho de Área**: Integrar `Leaflet.draw` no mapa para permitir desenhar polígonos (áreas) e salvar como GeoJSON vinculado à ação.
- **Validação Visual**: Exibir a área de atuação desenhada no mapa.
- **Relatório**: Criar uma view de relatório consolidado.

### 4. Validações e Regras de Negócio
- GPS ping a cada 10s (Isso é configuração do Traccar Client, mas a API deve suportar).
- Fotos com localização (já validado no frontend com HTML5 Geolocation, mas precisamos garantir no backend).
- Fotos dentro da área (verificar se a lat/lon da foto está dentro do polígono GeoJSON da ação).
- Bloquear envio sem GPS (já tem uma validação básica no JS, mas podemos reforçar).

## Plano de Ação

1. **Models**:
   - Criar `Turno` em `app/models/turno.py`.
   - Criar `AreaAtuacao` em `app/models/area_atuacao.py`.
   - Criar `FotoAuditoria` em `app/models/foto_auditoria.py`.
   - Atualizar `app/models/__init__.py`.
   - Gerar migration (`flask db migrate`) e aplicar (`flask db upgrade`).

2. **Endpoints API**:
   - Atualizar `/api/gps/receber` para verificar turnos ativos (opcional, ou apenas salvar).
   - Criar endpoints para gerenciar áreas (`/api/areas/<acao_id>`).
   - Criar endpoints para turnos (`/api/turnos/iniciar`, `/api/turnos/finalizar`).

3. **Frontend (Mapa)**:
   - Adicionar Leaflet.draw ao template `mapa/index.html` ou criar um específico para desenho `acoes/desenhar_area.html`.
   - Exibir o polígono da área no `mapa/index.html`.

4. **Relatórios**:
   - Criar rota `/auditorias/relatorio/<acao_id>`.
   - Criar template `auditorias/relatorio.html` que mostre o mapa com rastro, área, fotos e dados do turno.

5. **Validações**:
   - Adicionar função em `GpsService` ou novo service para verificar se ponto está dentro do polígono (Ray-casting algorithm ou biblioteca shapely/turf, mas para simplificar, usaremos lógica matemática simples ou apenas validação no frontend se necessário. Em Python, podemos usar ray casting para point in polygon).

# Relatório Técnico Consolidado - Refatoração Estratégica

**Data:** 28 de Março de 2026
**Autor:** Manus AI
**Branch de Segurança:** `refactor/backup-ante-mudancas`

Este documento detalha as implementações realizadas no repositório `panfletagemrelampago/gestao` em conformidade com os Passos 1, 2 e 3 do plano de refatoração estratégica. Todas as alterações foram executadas em lote no ambiente de rascunho (branch isolado) e aguardam validação para o envio (push) ao repositório remoto.

---

## 1. Passo 1: Unificação de Dados e Padronização de Tempo

### 1.1. Unificação de Modelos (`Auditoria` → `FotoAuditoria`)
O sistema apresentava duplicidade de registros entre os modelos `Auditoria` (legado) e `FotoAuditoria`. A refatoração centralizou a fonte de verdade em `FotoAuditoria`.

*   **Modelo `FotoAuditoria`:** Adicionada a coluna `acao_id` como chave estrangeira direta para `acoes_promocionais`, substituindo a ponte legada `auditoria_id`. Os campos de ownership (`usuario_id` e `cliente_id`) foram mantidos.
*   **Modelo `AcaoPromocional`:** Removida a relação legada com `Auditoria` e estabelecida a relação com `FotoAuditoria` via *backref* `fotos`.
*   **Módulo Web (`auditorias/routes.py`):** A rota de registro de fotos foi alterada para persistir exclusivamente em `FotoAuditoria`. A listagem de fotos e a exclusão foram migradas para operar sobre o novo modelo.
*   **Módulo API (`api/mapa.py`):** O endpoint `/api/mapa/fotos` foi reescrito para consultar `FotoAuditoria`, aplicando os mesmos filtros de ownership (admin, funcionário, cliente).
*   **Segurança (`security_helpers.py`):** A função `get_auditoria_segura` foi atualizada para validar acessos com base em `FotoAuditoria` e seu campo `usuario_id`.
*   **Limpeza do ORM:** O modelo `Auditoria` foi removido do carregamento global em `app/models/__init__.py`. A tabela física foi preservada no banco de dados para não corromper o histórico legado.

### 1.2. Padronização UTC
Havia uma mistura de `datetime.utcnow()` com helpers que aplicavam o fuso horário GMT-4 (Cuiabá) diretamente na persistência, causando inconsistências.

*   **Persistência Uniforme:** Implementada a função interna `_utcnow()` que retorna um `datetime` UTC *naive* (sem *tzinfo*). Todos os modelos (`Turno`, `FotoAuditoria`, `PosicaoGps`, `Veiculo`) e serviços (`TurnoService`, `GpsService`) foram padronizados para usar exclusivamente esta função ao gravar no banco de dados PostgreSQL.
*   **Camada de Exibição:** As funções `get_local_now()` e `to_local_tz()` foram mantidas em `TurnoService` e `auditorias/routes.py`, mas seu uso foi estritamente restrito à camada de exibição (templates HTML e relatórios). Nenhuma conversão de fuso ocorre mais antes da persistência.

---

## 2. Passo 2: Performance da API e Camada de Serviço

### 2.1. Refatoração para Service Layer e Validação de GPS
A lógica de manipulação de coordenadas estava acoplada às rotas da API. Além disso, o sistema sofria com gargalos de escrita e registros de "saltos impossíveis".

*   **Centralização no `GpsService`:** A rota `/gps` em `api/routes.py` foi enxugada. Toda a lógica de processamento foi movida para `GpsService.process_and_save_position()`.
*   **Filtro de Deslocamento Improvável:** Implementada uma validação que calcula a velocidade implícita entre o ponto anterior e o novo ponto. Se a velocidade exceder 200 km/h (`MAX_SPEED_KMH`), o ponto é considerado um erro do hardware do GPS e é descartado antes de atingir o banco de dados.
*   **Filtro de Ruído (Drift):** Mantida a lógica que descarta pontos com deslocamento inferior a 5 metros e velocidade abaixo de 1 km/h.

### 2.2. Serialização com Marshmallow
A montagem manual de dicionários JSON nas rotas da API era verbosa e propensa a erros.

*   **Criação de Schemas:** Criado o arquivo `app/schemas.py` contendo os schemas do Marshmallow para `PosicaoGps`, `FotoAuditoria` e `Turno`.
*   **Integração nas Rotas:** As rotas em `api/routes.py` e `api/mapa.py` foram refatoradas para utilizar os métodos `.dump()` dos schemas, padronizando as respostas JSON e facilitando a manutenção futura. O schema `FotoAuditoriaMapaSchema` foi criado especificamente para manter a compatibilidade de chaves (`lat`, `lng`, `img`) exigida pelo frontend do Leaflet.

### 2.3. Otimização de Banco de Dados
Para acelerar o carregamento dos mapas e consultas de histórico, foram criados índices compostos.

*   **Migration Alembic:** Gerado o script de migração `d1e2f3a4b5c6_refactor_passo1_passo2_indices_compostos.py`.
*   **Índices Criados:**
    *   `posicoes_gps`: Índice em `(device_id, data_hora DESC)`.
    *   `fotos_auditoria`: Índices em `(acao_id, data_hora DESC)` e `(turno_id, data_hora DESC)`.
*   **Backfill de Dados:** A migration inclui um comando SQL para preencher a nova coluna `acao_id` em `fotos_auditoria` a partir da relação existente com a tabela `turnos`.

---

## 3. Passo 3: Centralização de Heurísticas

### 3.1. Eliminação de Lógica Duplicada
A heurística de busca do veículo do líder da equipe estava duplicada em `TurnoService.iniciar_turno` e na rota de visualização de turnos (`auditorias/routes.py`).

*   **Nova Fonte da Verdade:** Criado o método de classe `buscar_para_lider(lider_equipe_id, lider)` no modelo `Veiculo`.
*   **Heurística de Três Etapas:** O método encapsula a lógica de:
    1.  Busca direta pelo vínculo explícito (`motorista_id`).
    2.  *Fallback* buscando pelo primeiro nome do líder no campo `modelo`.
    3.  *Fallback* final retornando qualquer veículo ativo.
*   **Refatoração dos Consumidores:** Tanto o `TurnoService` quanto o `auditorias/routes.py` foram atualizados para invocar este método único, garantindo consistência em todo o sistema.

---

## Conclusão e Próximos Passos

Todas as refatorações solicitadas foram implementadas com sucesso no branch `refactor/backup-ante-mudancas`. O código está mais limpo, performático e seguro, com responsabilidades bem definidas entre as camadas de modelo, serviço e rotas.

Aguardo a sua validação deste relatório. Assim que aprovado, solicitarei a autorização para realizar o *push* consolidado para o repositório no GitHub.

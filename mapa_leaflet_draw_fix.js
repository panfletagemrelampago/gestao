// =============================
// CORREÇÃO DO LEAFLET.DRAW
// Implementa eventos draw:edited e draw:deleted
// =============================

// Variável global para rastrear qual área está sendo editada
let areaEmEdicao = null;
let mapaAreasEditaveis = {}; // Mapear layer.id para area.id do backend

// Função auxiliar para obter o ID da área a partir de um layer
function obterIdAreaDoLayer(layer) {
    // Procurar no mapa de editáveis
    for (let layerId in mapaAreasEditaveis) {
        if (mapaAreasEditaveis[layerId] === layer) {
            return layerId;
        }
    }
    return null;
}

// Função para salvar edições de uma área
async function salvarEdicaoArea(areaId, novoGeoJson, novoNome = null, novaDescricao = null, novaCor = null) {
    try {
        mostrarToast('Salvando edições...', 'info');
        
        const payload = {
            geojson: novoGeoJson
        };
        
        if (novoNome !== null) payload.nome = novoNome;
        if (novaDescricao !== null) payload.descricao = novaDescricao;
        if (novaCor !== null) payload.cor = novaCor;
        
        const response = await fetch(`/api/mapa/areas/${areaId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        const data = await response.json();
        
        if (response.ok && data.status === 'sucesso') {
            mostrarToast('✅ Edições salvas com sucesso!', 'success');
            await carregarAreas();
            areaEmEdicao = null;
            return true;
        } else {
            mostrarToast('❌ Erro ao salvar edições: ' + (data.erro || 'Tente novamente.'), 'danger');
            return false;
        }
    } catch (err) {
        console.error("Erro ao salvar edições:", err);
        mostrarToast('❌ Erro de comunicação ao salvar edições.', 'danger');
        return false;
    }
}

// Função para excluir uma área
async function excluirAreaComConfirmacao(areaId) {
    if (!confirm('Deseja excluir esta área permanentemente?')) return;
    
    try {
        mostrarToast('Excluindo área...', 'info');
        const response = await fetch(`/api/mapa/areas/${areaId}`, { method: 'DELETE' });
        const data = await response.json();
        
        if (response.ok && data.status === 'sucesso') {
            mostrarToast('✅ Área excluída com sucesso!', 'success');
            
            // Remover do mapa
            if (mapaAreasEditaveis[areaId]) {
                layers.areas.removeLayer(mapaAreasEditaveis[areaId]);
                delete mapaAreasEditaveis[areaId];
            }
            
            // Atualizar contagem
            const countElem = document.getElementById('count-areas');
            countElem.textContent = parseInt(countElem.textContent) - 1;
            
            await carregarAreas();
        } else {
            mostrarToast('❌ Erro ao excluir: ' + (data.erro || 'Tente novamente.'), 'danger');
        }
    } catch (err) {
        console.error("Erro ao excluir área:", err);
        mostrarToast('❌ Erro de comunicação ao excluir área.', 'danger');
    }
}

// Função para criar um popup editável para uma área
function criarPopupEditavel(area) {
    const nomeArea = escapeHTML(area.nome) || 'Área sem nome';
    const descArea = escapeHTML(area.descricao) || 'Sem descrição';
    
    {% if current_user.tipo_usuario in ['admin', 'funcionario'] %}
    return `
        <div style="min-width:220px">
            <h6 class="mb-2 fw-bold text-primary">${nomeArea}</h6>
            <p class="mb-2 small">${descArea}</p>
            <div class="d-grid gap-2">
                <button onclick="abrirDialogoEdicao(${area.id})" class="btn btn-sm btn-warning rounded-pill">
                    <i class="fas fa-edit me-1"></i> Editar
                </button>
                <button onclick="excluirAreaComConfirmacao(${area.id})" class="btn btn-sm btn-danger rounded-pill">
                    <i class="fas fa-trash me-1"></i> Excluir
                </button>
            </div>
        </div>
    `;
    {% else %}
    return `
        <div style="min-width:180px">
            <h6 class="mb-1 fw-bold text-primary">${nomeArea}</h6>
            <p class="mb-0 small">${descArea}</p>
        </div>
    `;
    {% endif %}
}

// Função para abrir diálogo de edição
function abrirDialogoEdicao(areaId) {
    // Buscar a área no mapa
    const layer = mapaAreasEditaveis[areaId];
    if (!layer) {
        mostrarToast('❌ Área não encontrada no mapa.', 'danger');
        return;
    }
    
    // Fechar popup
    if (layer.closePopup) layer.closePopup();
    
    // Ativar modo de edição no Leaflet.draw
    // Simular clique no botão de edição
    const editButton = document.querySelector('.leaflet-draw-edit');
    if (editButton) {
        editButton.click();
        areaEmEdicao = areaId;
        mostrarToast('ℹ️ Modo de edição ativado. Clique na área para editar.', 'info');
    }
}

// Inicializar o Leaflet.draw com suporte a edição e exclusão
document.addEventListener('DOMContentLoaded', async () => {
    // ... código anterior de carregamento ...
    
    // Ferramentas de Desenho (apenas admin/funcionario)
    {% if current_user.tipo_usuario in ['admin', 'funcionario'] %}
    const drawControl = new L.Control.Draw({
        draw: {
            polyline: false, circle: false, circlemarker: false, marker: false,
            polygon: { allowIntersection: false, showArea: true },
            rectangle: { shapeOptions: { color: '#0d6efd' } }
        },
        edit: { featureGroup: layers.areas, remove: true }
    });
    map.addControl(drawControl);
    
    // ========== EVENTO: CRIAR NOVA ÁREA ==========
    map.on(L.Draw.Event.CREATED, e => {
        const layer = e.layer;
        layers.areas.addLayer(layer);
        salvarArea(layer);
    });
    
    // ========== EVENTO: EDITAR ÁREA EXISTENTE ==========
    map.on(L.Draw.Event.EDITED, async e => {
        const layers_editados = e.layers;
        
        layers_editados.eachLayer(async layer => {
            // Encontrar qual área foi editada
            let areaId = null;
            for (let id in mapaAreasEditaveis) {
                if (mapaAreasEditaveis[id] === layer) {
                    areaId = parseInt(id);
                    break;
                }
            }
            
            if (areaId) {
                const novoGeoJson = layer.toGeoJSON();
                await salvarEdicaoArea(areaId, novoGeoJson);
            }
        });
    });
    
    // ========== EVENTO: EXCLUIR ÁREA ==========
    map.on(L.Draw.Event.DELETED, async e => {
        const layers_deletados = e.layers;
        
        layers_deletados.eachLayer(async layer => {
            // Encontrar qual área foi deletada
            let areaId = null;
            for (let id in mapaAreasEditaveis) {
                if (mapaAreasEditaveis[id] === layer) {
                    areaId = parseInt(id);
                    break;
                }
            }
            
            if (areaId) {
                await excluirAreaComConfirmacao(areaId);
            }
        });
    });
    
    // ========== EVENTO: INICIAR EDIÇÃO ==========
    map.on(L.Draw.Event.EDITSTART, e => {
        mostrarToast('ℹ️ Modo de edição ativado. Clique e arraste para editar áreas.', 'info');
    });
    
    // ========== EVENTO: FINALIZAR EDIÇÃO ==========
    map.on(L.Draw.Event.EDITSTOP, e => {
        mostrarToast('ℹ️ Modo de edição desativado.', 'info');
    });
    
    // ========== EVENTO: INICIAR EXCLUSÃO ==========
    map.on(L.Draw.Event.DELETESTART, e => {
        mostrarToast('ℹ️ Modo de exclusão ativado. Clique em uma área para excluir.', 'info');
    });
    
    // ========== EVENTO: FINALIZAR EXCLUSÃO ==========
    map.on(L.Draw.Event.DELETESTOP, e => {
        mostrarToast('ℹ️ Modo de exclusão desativado.', 'info');
    });
    
    {% endif %}
});

// Função modificada para carregar áreas com suporte a edição
async function carregarAreasComEdicao() {
    try {
        const response = await fetch('/api/mapa/areas');
        const areas = await response.json();
        layers.areas.clearLayers();
        Object.keys(mapaAreasEditaveis).forEach(k => delete mapaAreasEditaveis[k]);
        
        let totalAreas = 0;
        areas.forEach(area => {
            if (!area.geojson) return;
            totalAreas++;
            
            const geoLayer = L.geoJSON(area.geojson, {
                style: { 
                    color: area.cor || "#0d6efd", 
                    weight: 3, 
                    opacity: 0.8, 
                    fillOpacity: 0.15 
                }
            }).addTo(layers.areas);
            
            // Armazenar referência para edição
            if (area.id) {
                mapaAreasEditaveis[area.id] = geoLayer;
            }
            
            // Bind popup com opções de edição
            geoLayer.bindPopup(criarPopupEditavel(area));
        });
        
        document.getElementById('count-areas').textContent = totalAreas;
    } catch (err) {
        console.error("Erro ao carregar áreas:", err);
    }
}

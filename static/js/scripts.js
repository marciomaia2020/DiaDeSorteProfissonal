// ===== FUNÇÃO PARA CAPTURAR REGRAS ESCOLHIDAS =====
function capturarRegrasEscolhidas() {
    const regras = {
        pares_impares: true,
        finais_iguais: true,
        sequencias: true,
        repeticoes: true,
        distribuicao_faixas: true
    };
    
    if (document.getElementById('regra_padrao_dezenas')) {
        regras.padrao_dezenas = document.getElementById('regra_padrao_dezenas').checked;
    } else {
        regras.padrao_dezenas = true;
    }
    
    if (document.getElementById('regra_numeros_gatilho')) {
        regras.numeros_gatilho = document.getElementById('regra_numeros_gatilho').checked;
    } else {
        regras.numeros_gatilho = false;
    }
    
    return regras;
}

// ===== FUNÇÃO PARA APLICAR CONFIGURAÇÃO RECOMENDADA =====
function aplicarConfigRecomendada() {
    const analises_recomendadas = ['analise_mapa_calor', 'analise_ausencias', 'analise_blocos'];
    
    document.querySelectorAll('input[id^="analise_"]').forEach(checkbox => {
        checkbox.checked = false;
    });
    
    analises_recomendadas.forEach(id => {
        const checkbox = document.getElementById(id);
        if (checkbox) checkbox.checked = true;
    });
    
    if (document.getElementById('regra_padrao_dezenas')) {
        document.getElementById('regra_padrao_dezenas').checked = true;
    }
    if (document.getElementById('regra_numeros_gatilho')) {
        document.getElementById('regra_numeros_gatilho').checked = true;
    }
    
    const quantidadeSelect = document.getElementById('quantidade');
    if (quantidadeSelect) {
        quantidadeSelect.value = '10';
    }
    
    mostrarMensagem('Configuração recomendada aplicada! (Inclui números gatilho)', 'success');
}

// ===== FUNÇÃO PARA LIMPAR TODAS AS OPÇÕES =====
function limparTodasOpcoes() {
    document.querySelectorAll('input[id^="analise_"]').forEach(checkbox => {
        checkbox.checked = false;
    });
    
    if (document.getElementById('regra_padrao_dezenas')) {
        document.getElementById('regra_padrao_dezenas').checked = false;
    }
    if (document.getElementById('regra_numeros_gatilho')) {
        document.getElementById('regra_numeros_gatilho').checked = false;
    }
    
    const quantidadeSelect = document.getElementById('quantidade');
    if (quantidadeSelect) {
        quantidadeSelect.value = '5';
    }
    
    mostrarMensagem('Opções desmarcadas! (5 regras obrigatórias permanecem sempre ativas)', 'info');
}

// ===== FUNÇÃO PARA GERAR PALPITES PERSONALIZADOS =====
async function gerarPalpitesPersonalizados() {
    const quantidade = document.getElementById('quantidade').value;
    const analises = capturarAnalisesSelecionadas();
    const regras = capturarRegrasEscolhidas();
    
    console.log('🎲 Gerando palpites com:', { quantidade, analises, regras });
    console.log('✅ 5 Regras obrigatórias sempre ativas:', regras);
    console.log('🎯 Números gatilho:', regras.numeros_gatilho ? 'ATIVADOS' : 'DESATIVADOS');
    
    const resultadoDiv = document.getElementById('palpites-gerados-avancados');
    resultadoDiv.innerHTML = '<div class="loading">🎲 Gerando palpites inteligentes com 5 regras obrigatórias...</div>';
    
    try {
        const response = await fetch('/api/gerar-palpites-personalizados', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                quantidade: parseInt(quantidade),
                analises: analises,
                regras: regras
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            exibirPalpitesAvancados(data);
            const gatilhoMsg = data.numeros_gatilho_funcionais ? ` (${data.total_jogos_com_gatilho} com números gatilho)` : '';
            const mesMsg = data.mes_sorte_unico ? ` | Mês: ${data.mes_sorte_unico}` : '';
            mostrarMensagem(`${data.total_gerados} palpites gerados com 5 regras obrigatórias${gatilhoMsg}${mesMsg}!`, 'success');
        } else {
            resultadoDiv.innerHTML = `<div class="error">❌ ${data.message}</div>`;
            mostrarMensagem(data.message, 'error');
        }
        
    } catch (error) {
        console.error('Erro ao gerar palpites:', error);
        resultadoDiv.innerHTML = '<div class="error">❌ Erro ao gerar palpites. Tente novamente.</div>';
        mostrarMensagem('Erro de conexão. Tente novamente.', 'error');
    }
}

// ===== FUNÇÃO PARA CAPTURAR ANÁLISES SELECIONADAS =====
function capturarAnalisesSelecionadas() {
    const analises = {};
    
    const checkboxes = [
        'analise_mapa_calor',
        'analise_ausencias',
        'analise_posicoes',
        'analise_irmas',
        'analise_sequencias_tubulares',
        'analise_finais',
        'analise_repiques',
        'analise_blocos'
    ];
    
    checkboxes.forEach(id => {
        const checkbox = document.getElementById(id);
        if (checkbox) {
            analises[id.replace('analise_', '')] = checkbox.checked;
        }
    });
    
    return analises;
}

// ===== FUNÇÃO PARA EXIBIR PALPITES AVANÇADOS COM SINALIZAÇÃO COMPLETA =====
function exibirPalpitesAvancados(data) {
    const resultadoDiv = document.getElementById('palpites-gerados-avancados');
    
    // Buscar dados para sinalização
    const ultimoSorteio = data.ultimo_sorteio_real ? data.ultimo_sorteio_real.dezenas : [];
    const numerosGatilho = data.numeros_gatilho_extraidos || [];
    const gatilhoAtivo = data.numeros_gatilho_funcionais || false;
    const mesEscolhido = data.mes_sorte_unico || 'N/A';
    
    let html = `
        <div class="palpites-resultado">
            <div class="palpites-header">
                <h3>🎯 Palpites com 5 Regras Obrigatórias (${data.total_gerados} jogos)</h3>
                <div class="estatisticas-rapidas">
                    <span class="stat">💰 Custo Total: R$ ${(data.total_gerados * 2.50).toFixed(2)}</span>
                    <span class="stat">✅ 5 Regras Sempre Aplicadas</span>
                    ${gatilhoAtivo ? `<span class="stat gatilho-ativo">🎯 Gatilhos: ${data.total_jogos_com_gatilho}/${data.total_gerados}</span>` : ''}
                    <span class="stat mes-ativo">📅 Mês: ${mesEscolhido}</span>
                </div>
                
                <!-- 🎨 LEGENDA COMPLETA DAS CORES -->
                <div class="legenda-cores">
                    <h4>🎨 Legenda das Cores:</h4>
                    <div class="legenda-items">
                        <div class="legenda-item">
                            <span class="numero par sample">PAR</span>
                            <span class="legenda-texto">Números Pares</span>
                        </div>
                        <div class="legenda-item">
                            <span class="numero impar sample">ÍMPAR</span>
                            <span class="legenda-texto">Números Ímpares</span>
                        </div>
                        <div class="legenda-item">
                            <span class="numero repetida sample">REP</span>
                            <span class="legenda-texto">🔄 Repetições do Último Sorteio</span>
                        </div>
                        <div class="legenda-item">
                            <span class="numero gatilho sample">GAT</span>
                            <span class="legenda-texto">🎯 Números Gatilho</span>
                        </div>
                    </div>
                    
<!-- 🌡️ INFORMAÇÕES DO MÊS DA SORTE ESTATÍSTICO -->
<div class="mes-sorte-info" style="font-weight: bold;">
    <h5>🌡️ MÊS DA SORTE ESCOLHIDO ESTATISTICAMENTE!</h5>
    <div class="mes-detalhes">
        <p><strong>📅 Mês escolhido para TODOS os palpites:</strong> 
            <span class="mes-escolhido">${mesEscolhido}</span>
        </p>
        <p><strong>🧮 Método:</strong> ${data.metodo_mes_sorte || 'Análise Estatística Completa'}</p>
        <p><strong>📊 Base de dados:</strong> Todos os concursos disponíveis com normalização robusta</p>
        <p><strong>📄 Exportação:</strong> Formato "01 02 03 04 05 06 07 ${data.mes_sorte_unico ? data.mes_sorte_unico.substring(0,3) : 'Mês'}"</p>
    </div>
</div>
                    
                    <!-- 🎯 INFORMAÇÕES DOS NÚMEROS GATILHO -->
                    ${gatilhoAtivo ? `
                        <div class="gatilho-info ativo">
                            <h5>🎯 NÚMEROS GATILHO ATIVOS!</h5>
                            <div class="gatilho-detalhes">
                                <p><strong>📊 Extraídos do último concurso:</strong></p>
                                <div class="numeros-gatilho-lista">
                                    ${numerosGatilho.map(n => `<span class="numero gatilho mini">${n.toString().padStart(2, '0')}</span>`).join(' ')}
                                </div>
                                <p><strong>🎲 Jogos com gatilhos:</strong> ${data.total_jogos_com_gatilho}/${data.total_gerados} (${((data.total_jogos_com_gatilho/data.total_gerados)*100).toFixed(1)}%)</p>
                            </div>
                        </div>
                    ` : `
                        <div class="gatilho-info desativado">
                            <h5>🎯 Números Gatilho DESATIVADOS</h5>
                            <p>Para ativar, marque a opção "🎯 Usar Números Gatilho" nas configurações.</p>
                        </div>
                    `}
                    
                    ${ultimoSorteio.length > 0 ? `
                        <div class="ultimo-sorteio-ref">
                            <strong>📊 Último Sorteio (Referência):</strong> 
                            ${ultimoSorteio.map(n => n.toString().padStart(2, '0')).join(' - ')}
                        </div>
                    ` : ''}
                </div>
            </div>
    `;
    
    // Palpites individuais
    data.palpites.forEach((palpite, index) => {
        const detalhes = palpite.detalhes;
        const gatilhosUsados = detalhes.numeros_gatilho_usados || [];
        
        // Mapeamento de mês para abreviação
        const mesesAbrev = {
            'Janeiro': 'Jan', 'Fevereiro': 'Fev', 'Março': 'Mar', 
            'Abril': 'Abr', 'Maio': 'Mai', 'Junho': 'Jun',
            'Julho': 'Jul', 'Agosto': 'Ago', 'Setembro': 'Set',
            'Outubro': 'Out', 'Novembro': 'Nov', 'Dezembro': 'Dez'
        };
        
        const mesAbrev = mesesAbrev[palpite.mes_sorte] || palpite.mes_sorte.substring(0,3);
        
        html += `
            <div class="palpite-item">
                <div class="palpite-header">
                    <h4>🎯 Jogo ${index + 1} - Força: ${palpite.forca} (${palpite.tentativas} tentativas)</h4>
                    ${gatilhosUsados.length > 0 ? `
                        <div class="gatilho-badge">
                            🎯 ${gatilhosUsados.length} Número${gatilhosUsados.length > 1 ? 's' : ''} Gatilho
                        </div>
                    ` : ''}
                </div>
                
                <!-- EXIBIÇÃO DO JOGO COMPLETO COMO SERÁ EXPORTADO -->
                <div class="jogo-completo-preview">
                    <strong>📄 Formato de Exportação:</strong>
                    <span class="jogo-exportacao">${palpite.dezenas.map(d => d.toString().padStart(2, '0')).join(' ')} ${mesAbrev}</span>
                </div>
                
                <div class="palpite-dezenas">
                    ${palpite.dezenas.map(num => {
                        const isPar = num % 2 === 0;
                        const isRepetida = ultimoSorteio.includes(num);
                        const isGatilho = gatilhosUsados.includes(num);
                        
                        let classes = ['numero'];
                        let title = '';
                        
                        // Prioridade: Gatilho > Repetição > Par/Ímpar
                        if (isGatilho) {
                            classes.push('gatilho');
                            title = `🎯 NÚMERO GATILHO (${num})`;
                        } else if (isRepetida) {
                            classes.push('repetida');
                            title = `🔄 REPETIÇÃO do último sorteio (${num})`;
                        } else if (isPar) {
                            classes.push('par');
                            title = `Par: ${num}`;
                        } else {
                            classes.push('impar');
                            title = `Ímpar: ${num}`;
                        }
                        
                        return `<span class="${classes.join(' ')}" title="${title}">${num.toString().padStart(2, '0')}</span>`;
                    }).join('')}
                </div>
                
                <div class="palpite-mes">
                    📅 Mês da Sorte: ${palpite.mes_sorte} (${mesAbrev})
                </div>
                
                <div class="palpite-detalhes">
                    <h5>📊 Análises: ${detalhes.analises_usadas.join(', ')}</h5>
                    
                    <div class="detalhes-grid">
                        <div class="detalhe-item">
                            <strong>⚖️ Distribuição:</strong> ${detalhes.distribuicao}
                        </div>
                        <div class="detalhe-item">
                            <strong>🔢 Finais Iguais:</strong> ${detalhes.finais_iguais}
                        </div>
                        <div class="detalhe-item">
                            <strong>🔗 Sequências:</strong> ${detalhes.sequencias}
                        </div>
                        <div class="detalhe-item">
                            <strong>🔄 Repetições:</strong> ${detalhes.repeticoes_ultimo}
                        </div>
                        <div class="detalhe-item">
                            <strong>➕ Soma:</strong> ${detalhes.soma}
                        </div>
                    </div>
                    
                    <!-- 🎯 DESTAQUE ESPECIAL DOS NÚMEROS GATILHO -->
                    ${gatilhosUsados.length > 0 ? `
                        <div class="gatilhos-destaque">
                            <strong>🎯 Números Gatilho Utilizados:</strong>
                            ${gatilhosUsados.map(n => 
                                `<span class="numero gatilho mini">${n.toString().padStart(2, '0')}</span>`
                            ).join(' ')}
                            <span class="gatilhos-count">(${gatilhosUsados.length} números)</span>
                        </div>
                    ` : ''}
                    
                    <!-- 🔄 DESTAQUE DAS REPETIÇÕES -->
                    ${detalhes.repeticoes_ultimo > 0 ? `
                        <div class="repeticoes-destaque">
                            <strong>🔄 Repetições do Último Sorteio:</strong>
                            ${palpite.dezenas.filter(n => ultimoSorteio.includes(n)).map(n => 
                                `<span class="numero repetida mini">${n.toString().padStart(2, '0')}</span>`
                            ).join(' ')}
                            <span class="repeticoes-count">(${detalhes.repeticoes_ultimo} números)</span>
                        </div>
                    ` : ''}
                    
                    <div class="regras-aplicadas">
                        <strong>📋 5 Regras Obrigatórias Aplicadas:</strong>
                        ${['Pares/Ímpares', 'Finais Iguais', 'Sequências', 'Repetições', 'Distribuição Faixas'].map(regra => 
                            `<span class="regra-tag">${regra}</span>`
                        ).join('')}
                        ${gatilhoAtivo ? `<span class="regra-tag gatilho">🎯 Números Gatilho</span>` : ''}
                    </div>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    resultadoDiv.innerHTML = html;
}

// ===== OUTRAS FUNÇÕES =====

function mostrarMensagem(mensagem, tipo = 'info') {
    let msgDiv = document.getElementById('mensagem-sistema');
    if (!msgDiv) {
        msgDiv = document.createElement('div');
        msgDiv.id = 'mensagem-sistema';
        msgDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 1rem 2rem;
            border-radius: 8px;
            color: white;
            font-weight: 600;
            z-index: 1000;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            transform: translateX(100%);
            transition: transform 0.3s ease;
            max-width: 300px;
            word-wrap: break-word;
        `;
        document.body.appendChild(msgDiv);
    }
    
    const cores = {
        success: '#27ae60',
        error: '#e74c3c',
        warning: '#f39c12',
        info: '#3498db'
    };
    
    msgDiv.style.background = cores[tipo] || cores.info;
    msgDiv.textContent = mensagem;
    msgDiv.style.transform = 'translateX(0)';
    
    setTimeout(() => {
        msgDiv.style.transform = 'translateX(100%)';
        setTimeout(() => {
            if (msgDiv.parentNode) {
                msgDiv.parentNode.removeChild(msgDiv);
            }
        }, 300);
    }, 4000);
}

function abrirModalRegras() {
    document.getElementById('modalRegras').style.display = 'block';
}

function fecharModalRegras() {
    document.getElementById('modalRegras').style.display = 'none';
}

window.onclick = function(event) {
    const modal = document.getElementById('modalRegras');
    if (event.target === modal) {
        modal.style.display = 'none';
    }
}

async function carregarHistorico() {
    try {
        mostrarMensagem('Carregando histórico...', 'info');
        
        const response = await fetch('/api/carregar-historico?limite=100');
        const data = await response.json();
        
        if (data.success) {
            mostrarMensagem(data.message, 'success');
        } else {
            mostrarMensagem(data.message, 'warning');
        }
    } catch (error) {
        console.error('Erro ao carregar histórico:', error);
        mostrarMensagem('Erro ao carregar histórico', 'error');
    }
}

async function carregarAnaliseAvancada(tipo) {
    try {
        const response = await fetch(`/api/analise-avancada?tipo=${tipo}`);
        const data = await response.json();
        
        const resultadoDiv = document.getElementById('resultado-analise-avancada');
        
        if (data.error) {
            resultadoDiv.innerHTML = `<div class="error">❌ ${data.error}</div>`;
            return;
        }
        
        let html = `<h4>📊 ${tipo.replace('_', ' ').toUpperCase()}</h4>`;
        
        if (tipo === 'mapa_calor') {
            html += '<div class="mapa-calor-resultado">';
            data.forEach(item => {
                const corStatus = item.status === 'quente' ? '#e74c3c' : 
                               item.status === 'morno' ? '#f39c12' : '#3498db';
                html += `
                    <div class="numero-calor" style="border-left: 4px solid ${corStatus}; padding: 0.5rem; margin: 0.5rem 0; background: white; border-radius: 4px;">
                        <strong>${item.numero}</strong> - ${item.status.toUpperCase()}
                        <small style="display: block; color: #666;">Freq: ${item.frequencia} | Lacuna: ${item.lacuna} | Temp: ${item.temperatura}%</small>
                    </div>
                `;
            });
            html += '</div>';
        } else if (tipo === 'pares_impares') {
            html += '<div class="pares-impares-resultado">';
            html += `<p><strong>Recomendação:</strong> ${data.recomendacao}</p>`;
            html += '<div class="distribuicoes-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem; margin-top: 1rem;">';
            Object.entries(data.distribuicoes).forEach(([dist, freq]) => {
                html += `<div class="distribuicao-item" style="background: white; padding: 0.75rem; border-radius: 6px; border-left: 3px solid #3498db; text-align: center;"><strong>${dist}</strong><br>${freq}x</div>`;
            });
            html += '</div></div>';
        } else {
            html += `<pre style="background: white; padding: 1rem; border-radius: 6px; overflow-x: auto;">${JSON.stringify(data, null, 2)}</pre>`;
        }
        
        resultadoDiv.innerHTML = html;
        mostrarMensagem(`Análise ${tipo} carregada!`, 'success');
        
    } catch (error) {
        console.error('Erro ao carregar análise:', error);
        document.getElementById('resultado-analise-avancada').innerHTML = 
            '<div class="error">❌ Erro ao carregar análise</div>';
        mostrarMensagem('Erro ao carregar análise', 'error');
    }
}

document.addEventListener('DOMContentLoaded', function() {
    console.log('🎯 Sistema Dia de Sorte COM MÊS ESTATÍSTICO VISÍVEL!');
    console.log('✅ 5 Regras OBRIGATÓRIAS sempre aplicadas');
    console.log('🔄 SINALIZAÇÃO VISUAL das repetições do último sorteio!');
    console.log('🎯 SINALIZAÇÃO VISUAL dos números gatilho!');
    console.log('📅 MÊS ESTATÍSTICO exibido na interface!');
    console.log('📄 EXPORTAÇÃO com formato: 01 02 03 04 05 06 07 Mês');
});
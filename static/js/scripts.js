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

// ===== FUNÇÃO CORRIGIDA PARA EXIBIR DADOS REAIS + PRÓXIMO SORTEIO =====
function exibirPalpitesAvancados(data) {
    const resultadoDiv = document.getElementById('palpites-gerados-avancados');
    
    // 📊 BUSCAR DADOS REAIS DA RESPOSTA DA API
    const ultimoSorteio = data.ultimo_sorteio_real ? data.ultimo_sorteio_real.dezenas : [];
    const numerosGatilho = data.numeros_gatilho_extraidos || [];
    const gatilhoAtivo = data.numeros_gatilho_funcionais || false;
    const mesEscolhido = data.mes_sorte_unico || 'N/A';
    
    // 🌐 OBTER DADOS REAIS DO ÚLTIMO SORTEIO DA API DA CAIXA
    const dadosReais = data.ultimo_sorteio_real || {};
    const numeroConcursoReal = dadosReais.numero || 'N/A';
    const dataReal = dadosReais.data || 'N/A';
    const valorReal = dadosReais.valor_arrecadado || 0;
    const mesReal = dadosReais.mes_sorte || 'N/A';
    
    // 💰 FORMATAR VALOR CORRETAMENTE
    const valorFormatado = valorReal ? 
        new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL',
            minimumFractionDigits: 2
        }).format(valorReal) : 'N/A';
    
    // 🎯 FORMATAR PRÊMIO ESTIMADO DO PRÓXIMO SORTEIO
    const premioProximoFormatado = dadosReais.proximo_premio_estimado ? 
        new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL',
            minimumFractionDigits: 2
        }).format(dadosReais.proximo_premio_estimado) : 'N/A';
    
    console.log('📊 DADOS REAIS DA API:', {
        concurso: numeroConcursoReal,
        data: dataReal,
        valor: valorFormatado,
        mes: mesReal,
        proximo_concurso: dadosReais.proximo_numero,
        proximo_data: dadosReais.proximo_data,
        proximo_premio: premioProximoFormatado,
        fonte: data.fonte_dados || 'API da Caixa'
    });
    
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
                
                <!-- 🎯 DADOS DO PRÓXIMO SORTEIO - DESTAQUE PRINCIPAL -->
                <div style="background: linear-gradient(135deg, #007bff, #0056b3); color: white; padding: 1.5rem; border-radius: 12px; margin: 1.5rem 0; box-shadow: 0 4px 12px rgba(0,123,255,0.3);">
                    <h4 style="color: white !important; margin-bottom: 1rem; font-size: 1.3rem; text-align: center;">🎯 PRÓXIMO SORTEIO</h4>
                    <div style="display: flex; justify-content: space-around; align-items: center; flex-wrap: wrap; gap: 1rem;">
                        <div style="text-align: center;">
                            <div style="font-size: 0.9rem; opacity: 0.9;">Concurso</div>
                            <div style="font-size: 1.8rem; font-weight: bold;">${dadosReais.proximo_numero || 'N/A'}</div>
                        </div>
                        <div style="text-align: center;">
                            <div style="font-size: 0.9rem; opacity: 0.9;">Data</div>
                            <div style="font-size: 1.2rem; font-weight: bold;">${dadosReais.proximo_data || 'N/A'}</div>
                        </div>
                        <div style="text-align: center;">
                            <div style="font-size: 0.9rem; opacity: 0.9;">Prêmio Estimado</div>
                            <div style="font-size: 1.4rem; font-weight: bold; color: #ffd700;">${premioProximoFormatado}</div>
                        </div>
                        <div style="text-align: center;">
                            <div style="font-size: 0.9rem; opacity: 0.9;">Mês da Sorte (Último)</div>
                            <div style="font-size: 1.2rem; font-weight: bold; color: #17a2b8;">${mesReal}</div>
                        </div>
                    </div>
                    <div style="text-align: center; margin-top: 1rem; padding: 0.5rem; background: rgba(255,255,255,0.1); border-radius: 6px;">
                        <small style="color: white !important;">📊 Campos: numeroConcursoProximo, dataProximoConcurso, valorEstimadoProximoConcurso + nomeTimeCoracaoMesSorte</small>
                    </div>
                </div>
                
                <!-- 🎨 LEGENDA COMPLETA DAS CORES -->
                <div class="legenda-cores" style="background: white !important; color: #2c3e50 !important; border: 2px solid #ddd !important; padding: 1.5rem; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
                    <h4 style="color: #2c3e50 !important; margin-bottom: 1rem; font-size: 1.2rem;">🎨 Legenda das Cores:</h4>
                    <div class="legenda-items" style="display: flex; flex-wrap: wrap; gap: 1.5rem;">
                        <div class="legenda-item" style="display: flex; align-items: center; gap: 0.5rem; background: white !important; padding: 0.75rem; border: 1px solid #e9ecef; border-radius: 8px;">
                            <span class="numero par sample">PAR</span>
                            <span class="legenda-texto" style="color: #2c3e50 !important; font-weight: 600;">Números Pares</span>
                        </div>
                        <div class="legenda-item" style="display: flex; align-items: center; gap: 0.5rem; background: white !important; padding: 0.75rem; border: 1px solid #e9ecef; border-radius: 8px;">
                            <span class="numero impar sample">ÍMP</span>
                            <span class="legenda-texto" style="color: #2c3e50 !important; font-weight: 600;">Números Ímpares</span>
                        </div>
                        <div class="legenda-item" style="display: flex; align-items: center; gap: 0.5rem; background: white !important; padding: 0.75rem; border: 1px solid #e9ecef; border-radius: 8px;">
                            <span class="numero repetida sample">REP</span>
                            <span class="legenda-texto" style="color: #2c3e50 !important; font-weight: 600;">🔄 Repetições do Último Sorteio</span>
                        </div>
                        <div class="legenda-item" style="display: flex; align-items: center; gap: 0.5rem; background: white !important; padding: 0.75rem; border: 1px solid #e9ecef; border-radius: 8px;">
                            <span class="numero gatilho sample">GAT</span>
                            <span class="legenda-texto" style="color: #2c3e50 !important; font-weight: 600;">🎯 Números Gatilho</span>
                        </div>
                    </div>
                    
                    <!-- 🌡️ INFORMAÇÕES DO MÊS DA SORTE ESTATÍSTICO -->
                    <div class="mes-sorte-info" style="font-weight: bold; margin-top: 1.5rem; background: rgba(255,255,255,0.95); padding: 1rem; border-radius: 8px; border: 2px solid #17a2b8;">
                        <h5 style="color: #2c3e50 !important;">🌡️ MÊS DA SORTE ESCOLHIDO ESTATISTICAMENTE!</h5>
                        <div class="mes-detalhes">
                            <p style="color: #2c3e50 !important;"><strong>📅 Mês escolhido para TODOS os palpites:</strong> 
                                <span class="mes-escolhido" style="color: #17a2b8 !important; font-weight: bold;">${mesEscolhido}</span>
                            </p>
                            <p style="color: #2c3e50 !important;"><strong>🧮 Método:</strong> ${data.metodo_mes_sorte || 'Análise Estatística Completa'}</p>
                            <p style="color: #2c3e50 !important;"><strong>📊 Base de dados:</strong> Todos os concursos disponíveis com normalização robusta</p>
                            <p style="color: #2c3e50 !important;"><strong>📄 Exportação:</strong> Formato "01 02 03 04 05 06 07 ${data.mes_sorte_unico ? data.mes_sorte_unico.substring(0,3) : 'Mês'}"</p>
                        </div>
                    </div>
                    
                    <!-- 🎯 NÚMEROS GATILHO COM DADOS REAIS -->
                    ${gatilhoAtivo ? `
                        <div class="gatilho-info ativo" style="margin-top: 1.5rem;">
                            <h5 style="color: #2c3e50 !important;">🎯 NÚMEROS GATILHO ATIVOS!</h5>
                            
                            <div style="display: flex; gap: 2rem; align-items: flex-start; flex-wrap: wrap;">
                                <!-- NÚMEROS GATILHO MENORES -->
                                <div style="flex: 1; min-width: 300px;">
                                    <p style="color: #6a1b9a !important; font-weight: 600; margin-bottom: 1rem;"><strong>📊 Extraídos do último concurso:</strong></p>
                                    <div class="numeros-gatilho-lista" style="margin: 1rem 0;">
                                        ${numerosGatilho.map(n => `<span class="numero gatilho" style="width: 30px; height: 30px; font-size: 0.8rem; margin: 0.2rem;">${n.toString().padStart(2, '0')}</span>`).join(' ')}
                                    </div>
                                    <p style="color: #6a1b9a !important; font-weight: 600;"><strong>🎲 Jogos com gatilhos:</strong> ${data.total_jogos_com_gatilho}/${data.total_gerados} (${((data.total_jogos_com_gatilho/data.total_gerados)*100).toFixed(1)}%)</p>
                                </div>
                                
                                <!-- 🎯 APENAS PRÓXIMO SORTEIO COM MÊS DA SORTE DO ÚLTIMO -->
                                <div style="flex: 1; min-width: 280px; background: rgba(255,255,255,0.95); padding: 1rem; border-radius: 8px; border: 2px solid #007bff; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                                    <p style="color: #2c3e50 !important; font-weight: 600; margin-bottom: 0.75rem; font-size: 0.95rem;">🎯 Próximo Sorteio:</p>
                                    <div style="display: flex; flex-direction: column; gap: 0.5rem;">
                                        <span style="color: #2c3e50 !important; font-size: 0.85rem; background: #f8f9fa; padding: 0.5rem; border-radius: 4px; display: flex; justify-content: space-between;">
                                            <strong style="color: #2c3e50 !important;">Concurso:</strong> 
                                            <span style="color: #fff !important; background: #007bff; padding: 0.2rem 0.5rem; border-radius: 3px; font-weight: bold;">${dadosReais.proximo_numero || 'N/A'}</span>
                                        </span>
                                        <span style="color: #2c3e50 !important; font-size: 0.85rem; background: #f8f9fa; padding: 0.5rem; border-radius: 4px; display: flex; justify-content: space-between;">
                                            <strong style="color: #2c3e50 !important;">Data:</strong> 
                                            <span style="color: #fff !important; background: #28a745; padding: 0.2rem 0.5rem; border-radius: 3px; font-weight: bold;">${dadosReais.proximo_data || 'N/A'}</span>
                                        </span>
                                        <span style="color: #2c3e50 !important; font-size: 0.85rem; background: #f8f9fa; padding: 0.5rem; border-radius: 4px; display: flex; justify-content: space-between;">
                                            <strong style="color: #2c3e50 !important;">Prêmio Estimado:</strong> 
                                            <span style="color: #212529 !important; background: #ffc107; padding: 0.2rem 0.5rem; border-radius: 3px; font-weight: bold;">
                                                ${dadosReais.proximo_premio_estimado ? 
                                                    new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(dadosReais.proximo_premio_estimado) 
                                                    : 'N/A'}
                                            </span>
                                        </span>
                                        <span style="color: #2c3e50 !important; font-size: 0.85rem; background: #f8f9fa; padding: 0.5rem; border-radius: 4px; display: flex; justify-content: space-between;">
                                            <strong style="color: #2c3e50 !important;">Mês da Sorte (Último):</strong> 
                                            <span style="color: #fff !important; background: #17a2b8; padding: 0.2rem 0.5rem; border-radius: 3px; font-weight: bold;">${mesReal}</span>
                                        </span>
                                    </div>
                                    <div style="margin-top: 0.75rem; padding: 0.5rem; background: #cce5ff; border-radius: 4px; border: 1px solid #99ccff;">
                                        <small style="color: #004085 !important; font-weight: 600;">🎯 Campos: numeroConcursoProximo, dataProximoConcurso, valorEstimadoProximoConcurso + nomeTimeCoracaoMesSorte</small>
                                    </div>
                                </div>
                            </div>
                        </div>
                    ` : `
                        <div class="gatilho-info desativado" style="margin-top: 1.5rem; background: rgba(255,255,255,0.95); padding: 1rem; border-radius: 8px; border: 2px solid #6c757d;">
                            <h5 style="color: #2c3e50 !important;">🎯 Números Gatilho DESATIVADOS</h5>
                            <p style="color: #2c3e50 !important;">Para ativar, marque a opção "🎯 Usar Números Gatilho" nas configurações.</p>
                            
                            <!-- 🎯 APENAS PRÓXIMO SORTEIO COM MÊS DA SORTE DO ÚLTIMO -->
                            <div style="margin-top: 1rem;">
                                <div style="max-width: 400px; margin: 0 auto; background: rgba(255,255,255,0.95); padding: 1rem; border-radius: 8px; border: 2px solid #007bff; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                                    <p style="color: #2c3e50 !important; font-weight: 600; margin-bottom: 0.75rem; font-size: 0.95rem;">🎯 Próximo Sorteio:</p>
                                    <div style="display: flex; flex-direction: column; gap: 0.5rem;">
                                        <span style="color: #2c3e50 !important; font-size: 0.85rem; background: #f8f9fa; padding: 0.5rem; border-radius: 4px; display: flex; justify-content: space-between;">
                                            <strong style="color: #2c3e50 !important;">Concurso:</strong> 
                                            <span style="color: #fff !important; background: #007bff; padding: 0.2rem 0.5rem; border-radius: 3px; font-weight: bold;">${dadosReais.proximo_numero || 'N/A'}</span>
                                        </span>
                                        <span style="color: #2c3e50 !important; font-size: 0.85rem; background: #f8f9fa; padding: 0.5rem; border-radius: 4px; display: flex; justify-content: space-between;">
                                            <strong style="color: #2c3e50 !important;">Data:</strong> 
                                            <span style="color: #fff !important; background: #28a745; padding: 0.2rem 0.5rem; border-radius: 3px; font-weight: bold;">${dadosReais.proximo_data || 'N/A'}</span>
                                        </span>
                                        <span style="color: #2c3e50 !important; font-size: 0.85rem; background: #f8f9fa; padding: 0.5rem; border-radius: 4px; display: flex; justify-content: space-between;">
                                            <strong style="color: #2c3e50 !important;">Prêmio Estimado:</strong> 
                                            <span style="color: #212529 !important; background: #ffc107; padding: 0.2rem 0.5rem; border-radius: 3px; font-weight: bold;">
                                                ${dadosReais.proximo_premio_estimado ? 
                                                    new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(dadosReais.proximo_premio_estimado) 
                                                    : 'N/A'}
                                            </span>
                                        </span>
                                        <span style="color: #2c3e50 !important; font-size: 0.85rem; background: #f8f9fa; padding: 0.5rem; border-radius: 4px; display: flex; justify-content: space-between;">
                                            <strong style="color: #2c3e50 !important;">Mês da Sorte (Último):</strong> 
                                            <span style="color: #fff !important; background: #17a2b8; padding: 0.2rem 0.5rem; border-radius: 3px; font-weight: bold;">${mesReal}</span>
                                        </span>
                                    </div>
                                    <div style="margin-top: 0.75rem; padding: 0.5rem; background: #cce5ff; border-radius: 4px; border: 1px solid #99ccff;">
                                        <small style="color: #004085 !important; font-weight: 600;">🎯 Campos: numeroConcursoProximo, dataProximoConcurso, valorEstimadoProximoConcurso + nomeTimeCoracaoMesSorte</small>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `}
                    
                    ${ultimoSorteio.length > 0 ? `
                        <div class="ultimo-sorteio-ref" style="background: rgba(255,255,255,0.95) !important; color: #2c3e50 !important; padding: 1rem; border-radius: 8px; border: 2px solid #007bff; margin-top: 1.5rem;">
                            <strong style="color: #2c3e50 !important;">📊 Último Sorteio REAL (Concurso ${numeroConcursoReal}):</strong> 
                            ${ultimoSorteio.map(n => n.toString().padStart(2, '0')).join(' - ')}
                        </div>
                    ` : ''}
                </div>
            </div>
    `;
    
    // [Resto da função permanece igual - palpites individuais...]
    data.palpites.forEach((palpite, index) => {
        const detalhes = palpite.detalhes;
        const gatilhosUsados = detalhes.numeros_gatilho_usados || [];
        
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
                    
                    ${gatilhosUsados.length > 0 ? `
                        <div class="gatilhos-destaque">
                            <strong>🎯 Números Gatilho Utilizados:</strong>
                            ${gatilhosUsados.map(n => 
                                `<span class="numero gatilho mini">${n.toString().padStart(2, '0')}</span>`
                            ).join(' ')}
                            <span class="gatilhos-count">(${gatilhosUsados.length} números)</span>
                        </div>
                    ` : ''}
                    
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
    console.log('🎯 Sistema Dia de Sorte COM DADOS REAIS DA API!');
    console.log('🌐 API DA CAIXA: https://servicebus2.caixa.gov.br/portaldeloterias/api/diadesorte');
    console.log('✅ DADOS SEMPRE REAIS - NUNCA FICTÍCIOS!');
    console.log('📊 CAMPOS INCLUÍDOS:');
    console.log('   📊 numero (do último concurso)');
    console.log('   📅 dataApuracao (do último sorteio)');
    console.log('   💰 valorArrecadado (do último concurso)');
    console.log('   📅 nomeTimeCoracaoMesSorte (mês da sorte)');
    console.log('🔄 SINALIZAÇÃO VISUAL das repetições do último sorteio!');
    console.log('🎯 SINALIZAÇÃO VISUAL dos números gatilho!');
    console.log('📅 MÊS ESTATÍSTICO exibido na interface!');
    console.log('📄 EXPORTAÇÃO com formato: 01 02 03 04 05 06 07 Mês');
});
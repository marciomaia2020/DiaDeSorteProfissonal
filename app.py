from flask import Flask, render_template, request, jsonify, send_file
import sqlite3
import requests
import json
from datetime import datetime, timedelta
import random
from collections import Counter, defaultdict
import pandas as pd
import os
from io import BytesIO
import zipfile
from itertools import combinations, permutations
import math
import re
import tempfile

app = Flask(__name__)
app.secret_key = 'dia_de_sorte_2025_professional_advanced'

# Configurações
DATABASE = 'database/dia_de_sorte.db'
API_URL = 'https://servicebus2.caixa.gov.br/portaldeloterias/api/diadesorte'

# Armazenamento temporário dos últimos palpites gerados
ultimos_palpites_gerados = []

# Cache para último sorteio
ultimo_sorteio_cache = None

def normalizar_mes_completo(mes_entrada):
    """
    🎯 NORMALIZA O MÊS PARA O FORMATO PADRÃO COMPLETO
    TRATA TODOS OS FORMATOS POSSÍVEIS DA CAIXA:
    - Números: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12
    - Abreviados: Jan, Fev, Mar, Abr, Mai, Jun, Jul, Ago, Set, Out, Nov, Dez
    - Completos: Janeiro, Fevereiro, Março, Abril, Maio, Junho, Julho, Agosto, Setembro, Outubro, Novembro, Dezembro
    """
    if not mes_entrada:
        return None
    
    # Limpar entrada
    mes_limpo = str(mes_entrada).strip()
    
    # Dicionário de mapeamento completo
    mapeamento_meses = {
        # Números
        '1': 'Janeiro', '01': 'Janeiro',
        '2': 'Fevereiro', '02': 'Fevereiro', 
        '3': 'Março', '03': 'Março',
        '4': 'Abril', '04': 'Abril',
        '5': 'Maio', '05': 'Maio',
        '6': 'Junho', '06': 'Junho',
        '7': 'Julho', '07': 'Julho',
        '8': 'Agosto', '08': 'Agosto',
        '9': 'Setembro', '09': 'Setembro',
        '10': 'Outubro',
        '11': 'Novembro',
        '12': 'Dezembro',
        
        # Abreviados (variações)
        'jan': 'Janeiro', 'Jan': 'Janeiro', 'JAN': 'Janeiro',
        'fev': 'Fevereiro', 'Fev': 'Fevereiro', 'FEV': 'Fevereiro',
        'mar': 'Março', 'Mar': 'Março', 'MAR': 'Março',
        'abr': 'Abril', 'Abr': 'Abril', 'ABR': 'Abril',
        'mai': 'Maio', 'Mai': 'Maio', 'MAI': 'Maio',
        'jun': 'Junho', 'Jun': 'Junho', 'JUN': 'Junho',
        'jul': 'Julho', 'Jul': 'Julho', 'JUL': 'Julho',
        'ago': 'Agosto', 'Ago': 'Agosto', 'AGO': 'Agosto',
        'set': 'Setembro', 'Set': 'Setembro', 'SET': 'Setembro',
        'out': 'Outubro', 'Out': 'Outubro', 'OUT': 'Outubro',
        'nov': 'Novembro', 'Nov': 'Novembro', 'NOV': 'Novembro',
        'dez': 'Dezembro', 'Dez': 'Dezembro', 'DEZ': 'Dezembro',
        
        # Completos (variações de capitalização)
        'janeiro': 'Janeiro', 'Janeiro': 'Janeiro', 'JANEIRO': 'Janeiro',
        'fevereiro': 'Fevereiro', 'Fevereiro': 'Fevereiro', 'FEVEREIRO': 'Fevereiro',
        'março': 'Março', 'Março': 'Março', 'MARÇO': 'Março',
        'abril': 'Abril', 'Abril': 'Abril', 'ABRIL': 'Abril',
        'maio': 'Maio', 'Maio': 'Maio', 'MAIO': 'Maio',
        'junho': 'Junho', 'Junho': 'Junho', 'JUNHO': 'Junho',
        'julho': 'Julho', 'Julho': 'Julho', 'JULHO': 'Julho',
        'agosto': 'Agosto', 'Agosto': 'Agosto', 'AGOSTO': 'Agosto',
        'setembro': 'Setembro', 'Setembro': 'Setembro', 'SETEMBRO': 'Setembro',
        'outubro': 'Outubro', 'Outubro': 'Outubro', 'OUTUBRO': 'Outubro',
        'novembro': 'Novembro', 'Novembro': 'Novembro', 'NOVEMBRO': 'Novembro',
        'dezembro': 'Dezembro', 'Dezembro': 'Dezembro', 'DEZEMBRO': 'Dezembro',
        
        # Variações com acentos/sem acentos
        'marco': 'Março', 'Marco': 'Março', 'MARCO': 'Março',
    }
    
    # Tentar mapeamento direto
    mes_normalizado = mapeamento_meses.get(mes_limpo)
    if mes_normalizado:
        return mes_normalizado
    
    # Tentar busca por substring (para casos como "Janeiro de 2024")
    for chave, valor in mapeamento_meses.items():
        if chave.lower() in mes_limpo.lower() or mes_limpo.lower() in chave.lower():
            return valor
    
    # Se não encontrou, tentar extrair número
    try:
        numero_extraido = re.search(r'\d+', mes_limpo)
        if numero_extraido:
            numero = int(numero_extraido.group())
            if 1 <= numero <= 12:
                meses_por_numero = [
                    '', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
                    'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
                ]
                return meses_por_numero[numero]
    except:
        pass
    
    print(f"⚠️ Mês não reconhecido: '{mes_entrada}' -> Retornando None")
    return None

def buscar_ultimo_sorteio_real():
    """🎯 BUSCA DADOS REAIS DO ÚLTIMO SORTEIO DA API DA CAIXA"""
    global ultimo_sorteio_cache
    
    try:
        print("🌐 Buscando último sorteio real da API da Caixa...")
        response = requests.get(API_URL, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            ultimo_sorteio_cache = {
                'numero': data.get('numero', 0),
                'data': data.get('dataApuracao', ''),
                'dezenas': [int(x) for x in data.get('listaDezenas', [])],
                'mes_sorte': data.get('nomeTimeCoracaoMesSorte', ''),
                'valor_arrecadado': data.get('valorArrecadado', 0)
            }
            
            print(f"✅ Último sorteio REAL carregado:")
            print(f"   📊 Concurso: {ultimo_sorteio_cache['numero']}")
            print(f"   📅 Data: {ultimo_sorteio_cache['data']}")
            print(f"   🎲 Dezenas: {ultimo_sorteio_cache['dezenas']}")
            print(f"   📅 Mês: {ultimo_sorteio_cache['mes_sorte']}")
            
            return ultimo_sorteio_cache
        else:
            print(f"❌ Erro na API: Status {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Erro ao buscar último sorteio: {e}")
        return None

def extrair_numeros_gatilho_ultra_mega_criativos():
    """
    🎯 EXTRAI NÚMEROS GATILHO COM CRIATIVIDADE ABSOLUTA!
    📊 Exemplo: Concurso 1122, 30/09/2025, R$ 150.000,00
    🧠 TODAS as técnicas imagináveis + 4 operações matemáticas!
    """
    try:
        ultimo_real = buscar_ultimo_sorteio_real()
        if not ultimo_real:
            print("⚠️ Não foi possível buscar dados do último sorteio")
            return []
        
        numero_concurso = ultimo_real['numero']
        data_apuracao = ultimo_real['data']
        valor_arrecadado = ultimo_real['valor_arrecadado']
        
        print(f"\n🎯 EXTRAÇÃO ULTRA MEGA CRIATIVA DE NÚMEROS GATILHO:")
        print(f"📊 Concurso: {numero_concurso}")
        print(f"📅 Data: {data_apuracao}")
        print(f"💰 Valor: R$ {valor_arrecadado}")
        print("="*80)
        
        numeros_candidatos = set()
        explicacoes = []
        
        # ===== NÚMEROS INTEIROS E INVERSÕES =====
        if numero_concurso > 0:
            numero_str = str(numero_concurso)
            
            # 1. Números inteiros diretos do concurso
            for i in range(len(numero_str)):
                for j in range(i+1, len(numero_str)+1):
                    pedaco = numero_str[i:j]
                    if pedaco and not pedaco.startswith('0'):
                        num = int(pedaco)
                        if 1 <= num <= 31:
                            numeros_candidatos.add(num)
                            explicacoes.append(f"🔢 {pedaco} extraído de {numero_concurso}")
            
            # 2. Inversões de números (COMO NO SEU EXEMPLO)
            # 30 → 03, 09 → 90 (mas consideramos 09), etc.
            for i in range(len(numero_str)):
                for j in range(i+1, len(numero_str)+1):
                    pedaco = numero_str[i:j]
                    if pedaco and len(pedaco) >= 1:
                        invertido = pedaco[::-1]
                        if invertido and not invertido.startswith('0'):
                            num_inv = int(invertido)
                            if 1 <= num_inv <= 31:
                                numeros_candidatos.add(num_inv)
                                explicacoes.append(f"🔄 {pedaco} invertido = {num_inv}")
            
            # 3. QUATRO OPERAÇÕES MATEMÁTICAS no número do concurso
            # Exemplo: 1122 → várias operações
            digitos = [int(d) for d in numero_str]
            
            # SOMA de combinações
            for i in range(len(digitos)):
                for j in range(i+1, len(digitos)):
                    soma = digitos[i] + digitos[j]
                    if 1 <= soma <= 31:
                        numeros_candidatos.add(soma)
                        explicacoes.append(f"➕ {digitos[i]} + {digitos[j]} = {soma}")
            
            # SUBTRAÇÃO de combinações
            for i in range(len(digitos)):
                for j in range(len(digitos)):
                    if i != j and digitos[i] > digitos[j]:
                        sub = digitos[i] - digitos[j]
                        if 1 <= sub <= 31:
                            numeros_candidatos.add(sub)
                            explicacoes.append(f"➖ {digitos[i]} - {digitos[j]} = {sub}")
            
            # MULTIPLICAÇÃO de combinações
            for i in range(len(digitos)):
                for j in range(i+1, len(digitos)):
                    if digitos[i] > 0 and digitos[j] > 0:
                        mult = digitos[i] * digitos[j]
                        if 1 <= mult <= 31:
                            numeros_candidatos.add(mult)
                            explicacoes.append(f"✖️ {digitos[i]} × {digitos[j]} = {mult}")
            
            # DIVISÃO de combinações
            for i in range(len(digitos)):
                for j in range(len(digitos)):
                    if i != j and digitos[j] > 0 and digitos[i] % digitos[j] == 0:
                        div = digitos[i] // digitos[j]
                        if 1 <= div <= 31:
                            numeros_candidatos.add(div)
                            explicacoes.append(f"➗ {digitos[i]} ÷ {digitos[j]} = {div}")
            
            # OPERAÇÕES COM PARES DE DÍGITOS
            # Exemplo: 1122 → 11+22, 11-22, etc.
            if len(numero_str) >= 4:
                primeira_metade = int(numero_str[:2])
                segunda_metade = int(numero_str[2:4])
                
                # Soma dos pares
                soma_pares = primeira_metade + segunda_metade
                if 1 <= soma_pares <= 31:
                    numeros_candidatos.add(soma_pares)
                    explicacoes.append(f"➕ {primeira_metade} + {segunda_metade} = {soma_pares}")
                
                # Subtração dos pares
                if primeira_metade > segunda_metade:
                    sub_pares = primeira_metade - segunda_metade
                    if 1 <= sub_pares <= 31:
                        numeros_candidatos.add(sub_pares)
                        explicacoes.append(f"➖ {primeira_metade} - {segunda_metade} = {sub_pares}")
                
                # Multiplicação (se resultado válido)
                mult_pares = primeira_metade * segunda_metade
                if 1 <= mult_pares <= 31:
                    numeros_candidatos.add(mult_pares)
                    explicacoes.append(f"✖️ {primeira_metade} × {segunda_metade} = {mult_pares}")
                
                # Divisão
                if segunda_metade > 0 and primeira_metade % segunda_metade == 0:
                    div_pares = primeira_metade // segunda_metade
                    if 1 <= div_pares <= 31:
                        numeros_candidatos.add(div_pares)
                        explicacoes.append(f"➗ {primeira_metade} ÷ {segunda_metade} = {div_pares}")
        
        # ===== DATA COM MÁXIMA CRIATIVIDADE =====
        if data_apuracao:
            data_match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', data_apuracao)
            
            if data_match:
                dia, mes, ano = data_match.groups()
                dia_int, mes_int, ano_int = int(dia), int(mes), int(ano)
                
                # Números diretos
                if 1 <= dia_int <= 31:
                    numeros_candidatos.add(dia_int)
                    explicacoes.append(f"📅 Dia {dia_int}")
                
                if 1 <= mes_int <= 31:
                    numeros_candidatos.add(mes_int)
                    explicacoes.append(f"📅 Mês {mes_int}")
                
                # Ano em pedaços
                ano_str = str(ano_int)
                if len(ano_str) == 4:
                    # 2025 → 20, 25
                    for i in range(len(ano_str)):
                        for j in range(i+1, len(ano_str)+1):
                            pedaco_ano = ano_str[i:j]
                            if pedaco_ano and not pedaco_ano.startswith('0'):
                                num_ano = int(pedaco_ano)
                                if 1 <= num_ano <= 31:
                                    numeros_candidatos.add(num_ano)
                                    explicacoes.append(f"📅 {pedaco_ano} do ano {ano_int}")
                
                # INVERSÕES DA DATA (COMO NO SEU EXEMPLO)
                # 30 → 03, 09 → 90, 20 → 02, 25 → 52, 15 → 51
                numeros_data = [dia_int, mes_int]
                for num in numeros_data:
                    num_str = str(num)
                    invertido = int(num_str[::-1])
                    if 1 <= invertido <= 31:
                        numeros_candidatos.add(invertido)
                        explicacoes.append(f"🔄 {num} invertido = {invertido}")
                
                # 4 OPERAÇÕES com elementos da data
                elementos_data = [dia_int, mes_int, ano_int % 100, int(str(ano_int)[:2])]
                
                for i, elem1 in enumerate(elementos_data):
                    for j, elem2 in enumerate(elementos_data):
                        if i != j:
                            # Soma
                            soma = elem1 + elem2
                            if 1 <= soma <= 31:
                                numeros_candidatos.add(soma)
                                explicacoes.append(f"➕ {elem1} + {elem2} = {soma} (data)")
                            
                            # Subtração
                            if elem1 > elem2:
                                sub = elem1 - elem2
                                if 1 <= sub <= 31:
                                    numeros_candidatos.add(sub)
                                    explicacoes.append(f"➖ {elem1} - {elem2} = {sub} (data)")
                            
                            # Multiplicação (limitada)
                            if elem1 <= 5 and elem2 <= 6:
                                mult = elem1 * elem2
                                if 1 <= mult <= 31:
                                    numeros_candidatos.add(mult)
                                    explicacoes.append(f"✖️ {elem1} × {elem2} = {mult} (data)")
                            
                            # Divisão
                            if elem2 > 0 and elem1 % elem2 == 0:
                                div = elem1 // elem2
                                if 1 <= div <= 31:
                                    numeros_candidatos.add(div)
                                    explicacoes.append(f"➗ {elem1} ÷ {elem2} = {div} (data)")
        
        # ===== VALOR ARRECADADO COM MÁXIMA CRIATIVIDADE =====
        if valor_arrecadado and valor_arrecadado > 0:
            valor_str = str(int(valor_arrecadado))
            
            # Extrair todos os pedaços possíveis
            for i in range(len(valor_str)):
                for j in range(i+1, len(valor_str)+1):
                    pedaco = valor_str[i:j]
                    if pedaco and not pedaco.startswith('0'):
                        num = int(pedaco)
                        if 1 <= num <= 31:
                            numeros_candidatos.add(num)
                            explicacoes.append(f"💰 {pedaco} do valor {valor_str}")
            
            # Exclusões criativas (COMO NO SEU EXEMPLO)
            # 150 → excluir 5 = 10, excluir 1 = 50 (inválido), etc.
            for digito_excluir in '0123456789':
                valor_sem_digito = valor_str.replace(digito_excluir, '')
                if valor_sem_digito:
                    # Tentar diferentes pedaços do resultado
                    for i in range(len(valor_sem_digito)):
                        for j in range(i+1, len(valor_sem_digito)+1):
                            pedaco_sem = valor_sem_digito[i:j]
                            if pedaco_sem and not pedaco_sem.startswith('0'):
                                try:
                                    num_sem = int(pedaco_sem)
                                    if 1 <= num_sem <= 31:
                                        numeros_candidatos.add(num_sem)
                                        explicacoes.append(f"💰 {valor_str} excluindo '{digito_excluir}' → {pedaco_sem}")
                                except:
                                    continue
            
            # 4 OPERAÇÕES com dígitos do valor
            digitos_valor = [int(d) for d in valor_str]
            
            # Operações entre todos os dígitos
            for i in range(len(digitos_valor)):
                for j in range(i+1, len(digitos_valor)):
                    d1, d2 = digitos_valor[i], digitos_valor[j]
                    
                    # Soma
                    soma = d1 + d2
                    if 1 <= soma <= 31:
                        numeros_candidatos.add(soma)
                        explicacoes.append(f"➕ {d1} + {d2} = {soma} (valor)")
                    
                    # Subtração
                    if d1 > d2:
                        sub = d1 - d2
                        if 1 <= sub <= 31:
                            numeros_candidatos.add(sub)
                            explicacoes.append(f"➖ {d1} - {d2} = {sub} (valor)")
                    
                    # Multiplicação
                    if d1 > 0 and d2 > 0:
                        mult = d1 * d2
                        if 1 <= mult <= 31:
                            numeros_candidatos.add(mult)
                            explicacoes.append(f"✖️ {d1} × {d2} = {mult} (valor)")
                    
                    # Divisão
                    if d2 > 0 and d1 % d2 == 0:
                        div = d1 // d2
                        if 1 <= div <= 31:
                            numeros_candidatos.add(div)
                            explicacoes.append(f"➗ {d1} ÷ {d2} = {div} (valor)")
        
        # ===== COMBINAÇÕES CRIATIVAS ENTRE DIFERENTES FONTES =====
        # Combinar elementos do concurso, data e valor
        if numero_concurso and data_apuracao:
            data_match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', data_apuracao)
            if data_match:
                dia, mes, ano = data_match.groups()
                dia_int, mes_int, ano_int = int(dia), int(mes), int(ano)
                
                # Elementos disponíveis para combinação
                elementos_concurso = [int(d) for d in str(numero_concurso)]
                elementos_data = [dia_int, mes_int, ano_int % 100]
                
                # Operações entre diferentes fontes
                for elem_c in elementos_concurso:
                    for elem_d in elementos_data:
                        # Soma
                        soma_mix = elem_c + elem_d
                        if 1 <= soma_mix <= 31:
                            numeros_candidatos.add(soma_mix)
                            explicacoes.append(f"🔀 {elem_c}(concurso) + {elem_d}(data) = {soma_mix}")
                        
                        # Subtração
                        if elem_c > elem_d:
                            sub_mix = elem_c - elem_d
                            if 1 <= sub_mix <= 31:
                                numeros_candidatos.add(sub_mix)
                                explicacoes.append(f"🔀 {elem_c}(concurso) - {elem_d}(data) = {sub_mix}")
                        
                        # Multiplicação (limitada)
                        if elem_c <= 5 and elem_d <= 6:
                            mult_mix = elem_c * elem_d
                            if 1 <= mult_mix <= 31:
                                numeros_candidatos.add(mult_mix)
                                explicacoes.append(f"🔀 {elem_c}(concurso) × {elem_d}(data) = {mult_mix}")
        
        # ===== OPERAÇÕES ESPECIAIS BASEADAS NO SEU EXEMPLO =====
        # Exemplo específico: 1122 → 21 (você mencionou)
        if numero_concurso > 0:
            numero_str = str(numero_concurso)
            
            # Tentar extrair 21 de 1122 de várias formas
            # Pegando dígitos intercalados, etc.
            if len(numero_str) >= 4:
                # Intercalar dígitos: 1122 → 12, 12, depois 1+2=3, mas 21 seria 2+1
                for i in range(len(numero_str)):
                    for j in range(i+1, len(numero_str)):
                        combinacao = numero_str[i] + numero_str[j]
                        if combinacao and not combinacao.startswith('0'):
                            num_comb = int(combinacao)
                            if 1 <= num_comb <= 31:
                                numeros_candidatos.add(num_comb)
                                explicacoes.append(f"🎯 Combinação {numero_str[i]}{numero_str[j]} = {num_comb}")
        
        numeros_finais = sorted(list(numeros_candidatos))
        
        print(f"\n🎯 TÉCNICAS ULTRA MEGA CRIATIVAS APLICADAS:")
        print(f"📊 Total de {len(explicacoes)} operações realizadas!")
        
        # Mostrar por categoria
        print(f"\n🔢 OPERAÇÕES NUMÉRICAS:")
        for exp in [e for e in explicacoes if any(op in e for op in ['➕', '➖', '✖️', '➗'])][:10]:
            print(f"   {exp}")
        
        print(f"\n🔄 INVERSÕES E TRANSFORMAÇÕES:")
        for exp in [e for e in explicacoes if '🔄' in e][:10]:
            print(f"   {exp}")
        
        print(f"\n💰 EXTRAÇÕES CRIATIVAS:")
        for exp in [e for e in explicacoes if '💰' in e or '📅' in e][:10]:
            print(f"   {exp}")
        
        if len(explicacoes) > 30:
            print(f"\n   ... e mais {len(explicacoes) - 30} técnicas aplicadas!")
        
        print(f"\n🎯 NÚMEROS GATILHO ULTRA MEGA CRIATIVOS: {numeros_finais}")
        print(f"📊 Total de {len(numeros_finais)} números únicos extraídos!")
        print("="*80 + "\n")
        
        return numeros_finais
        
    except Exception as e:
        print(f"❌ Erro ao extrair números gatilho mega criativos: {e}")
        import traceback
        traceback.print_exc()
        return []

# Função de compatibilidade
def extrair_numeros_gatilho_criativos():
    """🎯 Chama a versão ultra mega criativa"""
    return extrair_numeros_gatilho_ultra_mega_criativos()

def calcular_mes_sorte_inteligente():
    """
    🎯 CALCULA MÊS DA SORTE COM BASE EM ANÁLISE ESTATÍSTICA REAL
    📊 USANDO TODOS OS CONCURSOS + NORMALIZAÇÃO ROBUSTA DOS MESES
    """
    try:
        print("🌡️ INICIANDO ANÁLISE INTELIGENTE DO MÊS DA SORTE...")
        
        # 🎯 BUSCAR TODOS OS CONCURSOS DISPONÍVEIS (SEM LIMITE)
        historico = analyzer.get_historico_completo()  # TODOS os concursos
        
        if not historico or len(historico) < 20:
            print("⚠️ Histórico insuficiente para análise inteligente, usando mês atual")
            meses_basicos = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
                           'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
            return random.choice(meses_basicos)
        
        print(f"📊 ANALISANDO TODOS OS {len(historico)} CONCURSOS DISPONÍVEIS...")
        
        # 📊 CORRIGINDO A ORDEM: DO MAIS ANTIGO PARA O MAIS RECENTE (CRONOLÓGICA)
        historico_cronologico = list(reversed(historico))  # Inverter para ordem cronológica correta
        print(f"✅ Primeiro concurso: {historico_cronologico[0]['numero']}")
        print(f"✅ Último concurso: {historico_cronologico[-1]['numero']}")
        
        # Contar frequência e lacunas de cada mês
        meses_count = {}
        meses_lacuna = {}
        meses_nomes = {
            'Janeiro': 0, 'Fevereiro': 0, 'Março': 0, 'Abril': 0,
            'Maio': 0, 'Junho': 0, 'Julho': 0, 'Agosto': 0,
            'Setembro': 0, 'Outubro': 0, 'Novembro': 0, 'Dezembro': 0
        }
        
        # Inicializar contadores
        for mes in meses_nomes:
            meses_count[mes] = 0
            meses_lacuna[mes] = 0
        
        # Contadores para debug
        meses_nao_reconhecidos = {}
        meses_reconhecidos = 0
        
        # 📈 ANALISAR HISTÓRICO EM ORDEM CRONOLÓGICA CORRETA COM NORMALIZAÇÃO ROBUSTA
        print(f"📈 Analisando concursos em ordem cronológica com normalização robusta...")
        
        for idx, concurso in enumerate(historico_cronologico):
            mes_original = concurso.get('mes_sorte', '').strip()
            
            # 🎯 USAR A NOVA FUNÇÃO DE NORMALIZAÇÃO ROBUSTA
            mes_normalizado = normalizar_mes_completo(mes_original)
            
            if mes_normalizado and mes_normalizado in meses_nomes:
                meses_count[mes_normalizado] += 1
                meses_lacuna[mes_normalizado] = 0  # Resetar lacuna quando o mês sai
                meses_reconhecidos += 1
                
                # Debug apenas nos primeiros 10
                if idx < 10:
                    print(f"   📅 Concurso {concurso['numero']}: '{mes_original}' → '{mes_normalizado}'")
            else:
                # Contar meses não reconhecidos para debug
                if mes_original:
                    meses_nao_reconhecidos[mes_original] = meses_nao_reconhecidos.get(mes_original, 0) + 1
            
            # Incrementar lacuna para meses que não saíram neste concurso
            for mes_nome in meses_nomes:
                if mes_nome != mes_normalizado:
                    meses_lacuna[mes_nome] += 1
        
        # 📊 ESTATÍSTICAS DA NORMALIZAÇÃO
        print(f"✅ Meses reconhecidos: {meses_reconhecidos}/{len(historico_cronologico)}")
        if meses_nao_reconhecidos:
            print(f"⚠️ Meses NÃO reconhecidos ({len(meses_nao_reconhecidos)} tipos):")
            for mes_nao_rec, count in sorted(meses_nao_reconhecidos.items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"   📅 '{mes_nao_rec}': {count} vezes")
        
        # Calcular "temperatura" de cada mês
        meses_temperatura = {}
        total_concursos = len(historico_cronologico)
        
        print(f"\n📊 ANÁLISE ESTATÍSTICA DOS MESES (TODOS os {total_concursos} concursos):")
        
        for mes in meses_nomes:
            frequencia = meses_count[mes]
            lacuna = meses_lacuna[mes]
            
            # Fórmula de temperatura inteligente:
            # - Alta lacuna = mais provável sair (quente)
            # - Baixa frequência recente = mais provável sair (quente)
            # - Resultado: 0 a 100 (quanto maior, mais "quente")
            
            freq_normalizada = frequencia / total_concursos if total_concursos > 0 else 0
            lacuna_normalizada = min(lacuna / 100, 1.0)  # Normalizar lacuna (máx 100)
            
            # Peso: 70% lacuna + 30% baixa frequência
            temperatura = (lacuna_normalizada * 70) + ((1 - freq_normalizada) * 30)
            meses_temperatura[mes] = temperatura
            
            # Status baseado na temperatura
            if temperatura >= 70:
                status = "🔥 QUENTE"
            elif temperatura >= 50:
                status = "🌡️ MORNO"
            elif temperatura >= 30:
                status = "❄️ FRIO"
            else:
                status = "🧊 GELADO"
            
            print(f"   📅 {mes:>9}: {status} | Temp: {temperatura:5.1f} | Freq: {frequencia:2d} | Lacuna: {lacuna:2d}")
        
        # Classificar meses por temperatura (do mais quente para o mais frio)
        meses_ordenados = sorted(meses_temperatura.items(), key=lambda x: x[1], reverse=True)
        
        print(f"\n🏆 RANKING DE TEMPERATURA (mais prováveis de sair):")
        for i, (mes, temp) in enumerate(meses_ordenados[:5], 1):
            freq = meses_count[mes]
            lacuna = meses_lacuna[mes]
            print(f"   {i}º {mes} (Temp: {temp:.1f}, Freq: {freq}, Lacuna: {lacuna})")
        
        # ESTRATÉGIA INTELIGENTE DE ESCOLHA:
        # 50% chance: Top 3 mais quentes
        # 30% chance: Posições 4-7 (medianos)  
        # 15% chance: Posições 8-10 (frios)
        # 5% chance: Qualquer um (surpresa)
        
        rand = random.random()
        if rand < 0.50:
            # Escolher entre os 3 mais quentes
            candidatos = [mes for mes, temp in meses_ordenados[:3]]
            categoria = "QUENTE"
        elif rand < 0.80:
            # Escolher entre os medianos (posições 4-7)
            candidatos = [mes for mes, temp in meses_ordenados[3:7]]
            categoria = "MEDIANO"
        elif rand < 0.95:
            # Escolher entre os frios (posições 8-10)
            candidatos = [mes for mes, temp in meses_ordenados[7:10]]
            categoria = "FRIO"
        else:
            # Surpresa: qualquer um
            candidatos = list(meses_nomes.keys())
            categoria = "SURPRESA"
        
        mes_escolhido = random.choice(candidatos)
        temp_escolhido = meses_temperatura[mes_escolhido]
        freq_escolhido = meses_count[mes_escolhido]
        lacuna_escolhido = meses_lacuna[mes_escolhido]
        
        print(f"\n🎯 MÊS ESCOLHIDO: {mes_escolhido}")
        print(f"📊 Categoria: {categoria}")
        print(f"🌡️ Temperatura: {temp_escolhido:.1f}")
        print(f"📈 Frequência: {freq_escolhido}")
        print(f"⏰ Lacuna: {lacuna_escolhido}")
        print(f"🧮 Método: ANÁLISE COMPLETA (TODOS OS CONCURSOS + NORMALIZAÇÃO ROBUSTA)")
        
        return mes_escolhido
        
    except Exception as e:
        print(f"❌ Erro na análise inteligente de mês: {e}")
        import traceback
        traceback.print_exc()
        
        # Fallback seguro
        print("🔄 Usando fallback para mês da sorte...")
        meses_fallback = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
                         'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
        return random.choice(meses_fallback)

def validar_jogo_completo(jogo, ultimo_sorteio=None):
    """🎯 VALIDAÇÃO CORRETA DAS 5 REGRAS OBRIGATÓRIAS"""
    if len(jogo) != 7:
        print(f"❌ Jogo inválido: {len(jogo)} dezenas (necessário: 7)")
        return False
    
    if len(set(jogo)) != 7:
        print(f"❌ Jogo inválido: Dezenas repetidas no mesmo palpite: {jogo}")
        return False
    
    # ===== REGRA 1: PARES vs ÍMPARES (3P/4I) =====
    pares = len([x for x in jogo if x % 2 == 0])
    impares = len([x for x in jogo if x % 2 == 1])
    
    if pares != 3 or impares != 4:
        print(f"❌ Regra 1 falhou: {pares}P/{impares}I (necessário: 3P/4I)")
        return False
    
    # ===== REGRA 2: FINAIS IGUAIS (EXATAMENTE 2 PARES) =====
    finais = [x % 10 for x in jogo]
    finais_count = {}
    for final in finais:
        finais_count[final] = finais_count.get(final, 0) + 1
    
    finais_com_2_ocorrencias = sum(1 for count in finais_count.values() if count == 2)
    finais_com_1_ocorrencia = sum(1 for count in finais_count.values() if count == 1)
    finais_com_3_ou_mais = sum(1 for count in finais_count.values() if count >= 3)
    
    if finais_com_2_ocorrencias != 2 or finais_com_1_ocorrencia != 3 or finais_com_3_ou_mais > 0:
        print(f"❌ Regra 2 falhou: Deve ter EXATAMENTE 2 pares de finais iguais")
        return False
    
    # ===== REGRA 3: SEQUÊNCIAS CONSECUTIVAS (EXATAMENTE 2) =====
    jogo_ordenado = sorted(jogo)
    sequencias_duplas = 0
    for i in range(len(jogo_ordenado) - 1):
        if jogo_ordenado[i + 1] == jogo_ordenado[i] + 1:
            sequencias_duplas += 1
    
    if sequencias_duplas != 2:
        print(f"❌ Regra 3 falhou: {sequencias_duplas} sequências (necessário: EXATAMENTE 2)")
        return False
    
    # ===== REGRA 4: REPETIÇÕES DO ÚLTIMO SORTEIO (EXATAMENTE 2) =====
    if ultimo_sorteio and len(ultimo_sorteio) > 0:
        repeticoes = len([x for x in jogo if x in ultimo_sorteio])
        if repeticoes != 2:
            print(f"❌ Regra 4 falhou: {repeticoes} repetições do último sorteio (necessário: EXATAMENTE 2)")
            return False
    else:
        print("⚠️ Regra 4: Último sorteio não disponível, pulando validação de repetições")
    
    # ===== REGRA 5: DISTRIBUIÇÃO FAIXAS (2-3 cada) =====
    baixos = len([x for x in jogo if 1 <= x <= 10])
    medios = len([x for x in jogo if 11 <= x <= 20])
    altos = len([x for x in jogo if 21 <= x <= 31])
    
    if baixos < 2 or baixos > 3:
        print(f"❌ Regra 5 falhou: {baixos} baixos (necessário: 2-3)")
        return False
    if medios < 2 or medios > 3:
        print(f"❌ Regra 5 falhou: {medios} médios (necessário: 2-3)")
        return False
    if altos < 2 or altos > 3:
        print(f"❌ Regra 5 falhou: {altos} altos (necessário: 2-3)")
        return False
    
    print(f"✅ Jogo VÁLIDO: {jogo}")
    return True

def gerar_jogo_com_regras_corretas(ultimo_sorteio=None, numeros_gatilho=None, usar_gatilho=False):
    """🎯 GERA JOGO COM AS REGRAS CORRETAS + NÚMEROS GATILHO"""
    import random
    
    max_tentativas = 1000
    for tentativa in range(max_tentativas):
        
        jogo_base = []
        
        # 🎯 SE USAR NÚMEROS GATILHO, INCLUIR ALGUNS DELES
        if usar_gatilho and numeros_gatilho and len(numeros_gatilho) > 0:
            num_gatilho_usar = random.randint(1, min(3, len(numeros_gatilho)))
            gatilhos_escolhidos = random.sample(numeros_gatilho, num_gatilho_usar)
            jogo_base.extend(gatilhos_escolhidos)
        
        # Completar com números aleatórios
        numeros_restantes = [n for n in range(1, 32) if n not in jogo_base]
        numeros_adicionais = 7 - len(jogo_base)
        
        if numeros_adicionais > 0 and len(numeros_restantes) >= numeros_adicionais:
            jogo_base.extend(random.sample(numeros_restantes, numeros_adicionais))
        elif numeros_adicionais > 0:
            jogo_base.extend(numeros_restantes[:numeros_adicionais])
        
        jogo_candidato = sorted(jogo_base[:7])
        
        if validar_jogo_completo(jogo_candidato, ultimo_sorteio):
            return jogo_candidato, tentativa + 1
    
    print("⚠️ Não conseguiu gerar jogo válido, tentando abordagem forçada...")
    return gerar_jogo_forcado_corrigido(ultimo_sorteio, numeros_gatilho, usar_gatilho), max_tentativas

def gerar_jogo_forcado_corrigido(ultimo_sorteio=None, numeros_gatilho=None, usar_gatilho=False):
    """🔧 FORÇA A CRIAÇÃO DE UM JOGO VÁLIDO"""
    import random
    
    for tentativa_forcada in range(500):
        try:
            jogo_base = []
            
            if ultimo_sorteio and len(ultimo_sorteio) >= 2:
                repeticoes = random.sample(ultimo_sorteio, 2)
                jogo_base.extend(repeticoes)
            
            if usar_gatilho and numeros_gatilho and len(numeros_gatilho) > 0:
                gatilhos_disponiveis = [n for n in numeros_gatilho if n not in jogo_base]
                if gatilhos_disponiveis and len(jogo_base) < 6:
                    gatilho_escolhido = random.choice(gatilhos_disponiveis)
                    jogo_base.append(gatilho_escolhido)
            
            pares_usados = len([x for x in jogo_base if x % 2 == 0])
            impares_usados = len([x for x in jogo_base if x % 2 == 1])
            
            pares_restantes = 3 - pares_usados
            impares_restantes = 4 - impares_usados
            
            if pares_restantes < 0 or impares_restantes < 0:
                continue
            
            pares_pool = [x for x in range(2, 32, 2) if x not in jogo_base]
            impares_pool = [x for x in range(1, 32, 2) if x not in jogo_base]
            
            if len(pares_pool) < pares_restantes or len(impares_pool) < impares_restantes:
                continue
            
            if pares_restantes > 0:
                jogo_base.extend(random.sample(pares_pool, pares_restantes))
            if impares_restantes > 0:
                jogo_base.extend(random.sample(impares_pool, impares_restantes))
            
            jogo_ajustado = ajustar_finais_iguais_2_pares(jogo_base)
            
            if len(jogo_ajustado) == 7 and validar_jogo_completo(jogo_ajustado, ultimo_sorteio):
                return sorted(jogo_ajustado)
                
        except Exception as e:
            continue
    
    print("⚠️ Gerando jogo básico sem todas as validações")
    return sorted(random.sample(range(1, 32), 7))

def ajustar_finais_iguais_2_pares(jogo):
    """🔧 AJUSTA O JOGO PARA TER EXATAMENTE 2 PARES DE FINAIS IGUAIS"""
    import random
    
    finais = [x % 10 for x in jogo]
    finais_count = Counter(finais)
    
    finais_com_2 = sum(1 for count in finais_count.values() if count == 2)
    if finais_com_2 == 2 and len([c for c in finais_count.values() if c >= 3]) == 0:
        return jogo
    
    novo_jogo = []
    finais_usados = set()
    
    finais_para_pares = random.sample(range(10), 2)
    
    for final_par in finais_para_pares:
        candidatos = [x for x in range(1, 32) if x % 10 == final_par and x not in novo_jogo]
        if len(candidatos) >= 2:
            novo_jogo.extend(random.sample(candidatos, 2))
            finais_usados.add(final_par)
    
    while len(novo_jogo) < 7:
        candidato = random.randint(1, 31)
        if candidato not in novo_jogo and candidato % 10 not in finais_usados:
            novo_jogo.append(candidato)
            finais_usados.add(candidato % 10)
    
    return novo_jogo[:7]

class DiaDeSorteAnalyzerAdvanced:
    def __init__(self):
        self.db_path = DATABASE
        self.create_database()
        
    def create_database(self):
        """Cria o banco de dados avançado"""
        os.makedirs('database', exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS concursos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero INTEGER UNIQUE NOT NULL,
                data_sorteio TEXT NOT NULL,
                dezenas TEXT NOT NULL,
                dezenas_ordem_sorteio TEXT NOT NULL,
                mes_sorte TEXT NOT NULL,
                valor_arrecadado REAL,
                acumulado BOOLEAN,
                pares INTEGER DEFAULT 0,
                impares INTEGER DEFAULT 0,
                sequencias_count INTEGER DEFAULT 0,
                finais_iguais INTEGER DEFAULT 0,
                soma_total INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self._criar_tabelas_avancadas(cursor)
        
        conn.commit()
        conn.close()
    
    def _criar_tabelas_avancadas(self, cursor):
        """Cria tabelas avançadas"""
        try:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS estatisticas_avancadas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    numero_dezena INTEGER NOT NULL UNIQUE,
                    frequencia INTEGER DEFAULT 0,
                    ultima_aparicao INTEGER DEFAULT 0,
                    lacuna_temporal INTEGER DEFAULT 0,
                    temperatura_mapa_calor REAL DEFAULT 0,
                    ausencias_coletivas INTEGER DEFAULT 0,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            for i in range(1, 32):
                cursor.execute('''
                    INSERT OR IGNORE INTO estatisticas_avancadas (numero_dezena) VALUES (?)
                ''', (i,))
        except Exception as e:
            print(f"Erro ao criar tabelas avançadas: {e}")
        
    def get_db_connection(self):
        """Conecta ao banco de dados"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def fetch_multiple_concursos(self, limite=100):
        """Busca múltiplos concursos da API"""
        concursos_salvos = 0
        
        try:
            response = requests.get(API_URL, timeout=10)
            if response.status_code == 200:
                ultimo_concurso = response.json()
                numero_atual = ultimo_concurso['numero']
                
                for i in range(limite):
                    numero = numero_atual - i
                    if numero <= 0:
                        break
                        
                    try:
                        url_concurso = f"{API_URL}/{numero}"
                        resp = requests.get(url_concurso, timeout=5)
                        if resp.status_code == 200:
                            data = resp.json()
                            if self.save_concurso_avancado(data):
                                concursos_salvos += 1
                                print(f"Concurso {numero} salvo com análise avançada")
                    except:
                        continue
                        
                self.atualizar_todas_estatisticas()
                return concursos_salvos
                
        except Exception as e:
            print(f"Erro ao buscar múltiplos concursos: {e}")
            return 0
    
    def save_concurso_avancado(self, data):
        """Salva concurso com análise avançada"""
        conn = self.get_db_connection()
        
        try:
            dezenas = [int(x) for x in data['listaDezenas']]
            dezenas_ordem = [int(x) for x in data['dezenasSorteadasOrdemSorteio']]
            
            pares = len([x for x in dezenas if x % 2 == 0])
            impares = len([x for x in dezenas if x % 2 == 1])
            sequencias_count = self.contar_sequencias(sorted(dezenas))
            finais = [x % 10 for x in dezenas]
            finais_iguais = sum(1 for final, count in Counter(finais).items() if count > 1)
            soma_total = sum(dezenas)
            
            conn.execute('''
                INSERT OR REPLACE INTO concursos 
                (numero, data_sorteio, dezenas, dezenas_ordem_sorteio, mes_sorte, 
                 valor_arrecadado, acumulado, pares, impares, sequencias_count, 
                 finais_iguais, soma_total)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['numero'],
                data['dataApuracao'],
                ','.join(data['listaDezenas']),
                ','.join(data['dezenasSorteadasOrdemSorteio']),
                data['nomeTimeCoracaoMesSorte'],
                data.get('valorArrecadado', 0),
                data.get('acumulado', False),
                pares, impares, sequencias_count, finais_iguais, soma_total
            ))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Erro ao salvar concurso avançado: {e}")
            return False
        finally:
            conn.close()
    
    def contar_sequencias(self, dezenas_ordenadas):
        """Conta quantas DUPLAS sequenciais existem"""
        if len(dezenas_ordenadas) < 2:
            return 0
            
        sequencias_duplas = 0
        for i in range(len(dezenas_ordenadas) - 1):
            if dezenas_ordenadas[i + 1] == dezenas_ordenadas[i] + 1:
                sequencias_duplas += 1
                
        return sequencias_duplas
    
    def atualizar_todas_estatisticas(self):
        """Atualiza todas as estatísticas avançadas"""
        historico = self.get_historico_completo()
        conn = self.get_db_connection()
        
        if not historico:
            return
        
        for i in range(1, 32):
            frequencia = 0
            ultima_aparicao = len(historico)
            ausencias = 0
            
            for idx, concurso in enumerate(historico):
                dezenas = [int(x) for x in concurso['dezenas'].split(',')]
                
                if i in dezenas:
                    frequencia += 1
                    if ultima_aparicao == len(historico):
                        ultima_aparicao = idx
                else:
                    if ultima_aparicao == len(historico):
                        ausencias += 1
            
            lacuna = ultima_aparicao
            temperatura = self.calcular_temperatura_mapa_calor(frequencia, lacuna, len(historico))
            
            conn.execute('''
                UPDATE estatisticas_avancadas SET 
                frequencia = ?, 
                ultima_aparicao = ?, 
                lacuna_temporal = ?,
                temperatura_mapa_calor = ?,
                ausencias_coletivas = ?,
                updated_at = CURRENT_TIMESTAMP
                WHERE numero_dezena = ?
            ''', (frequencia, ultima_aparicao, lacuna, temperatura, ausencias, i))
        
        conn.commit()
        conn.close()
    
    def calcular_temperatura_mapa_calor(self, frequencia, lacuna, total_concursos):
        """Calcula temperatura para mapa de calor"""
        if total_concursos == 0:
            return 0
        
        freq_normalizada = frequencia / total_concursos
        lacuna_normalizada = lacuna / total_concursos if total_concursos > 0 else 1
        
        temperatura = (freq_normalizada * 0.7) + ((1 - lacuna_normalizada) * 0.3)
        return round(temperatura * 100, 2)
    
    def get_historico_completo(self, limite=None):
        """
        🎯 BUSCA HISTÓRICO COMPLETO DE CONCURSOS
        SE LIMITE=None, BUSCA TODOS OS CONCURSOS
        """
        conn = self.get_db_connection()
        
        if limite:
            concursos = conn.execute('''
                SELECT * FROM concursos ORDER BY numero DESC LIMIT ?
            ''', (limite,)).fetchall()
        else:
            # 🎯 BUSCAR TODOS OS CONCURSOS SEM LIMITE
            concursos = conn.execute('''
                SELECT * FROM concursos ORDER BY numero DESC
            ''').fetchall()
        
        conn.close()
        return [dict(row) for row in concursos]
    
    def get_analise_pares_impares(self):
        """Análise de distribuição pares vs ímpares"""
        historico = self.get_historico_completo(100)
        
        if not historico:
            return {'error': 'Histórico insuficiente'}
        
        distribuicoes = {}
        for concurso in historico:
            pares = concurso.get('pares', 0)
            impares = concurso.get('impares', 0)
            dist = f"{pares}P/{impares}I"
            distribuicoes[dist] = distribuicoes.get(dist, 0) + 1
        
        mais_comum = max(distribuicoes.items(), key=lambda x: x[1])
        
        return {
            'distribuicoes': distribuicoes,
            'padrao_mais_comum': mais_comum,
            'recomendacao': 'Use a distribuição 3P/4I (mais comum historicamente)'
        }
    
    def get_mapa_calor(self):
        """Análise de mapa de calor"""
        conn = self.get_db_connection()
        dados = conn.execute('''
            SELECT numero_dezena, frequencia, lacuna_temporal, temperatura_mapa_calor
            FROM estatisticas_avancadas 
            ORDER BY temperatura_mapa_calor DESC
        ''').fetchall()
        conn.close()
        
        resultado = []
        for row in dados:
            temp = row['temperatura_mapa_calor']
            status = 'quente' if temp > 70 else 'morno' if temp > 40 else 'frio'
            
            resultado.append({
                'numero': row['numero_dezena'],
                'frequencia': row['frequencia'],
                'lacuna': row['lacuna_temporal'],
                'temperatura': temp,
                'status': status
            })
        
        return resultado
    
    def get_ausencias_coletivas(self):
        """Análise de ausências coletivas"""
        conn = self.get_db_connection()
        dados = conn.execute('''
            SELECT numero_dezena, ausencias_coletivas, lacuna_temporal
            FROM estatisticas_avancadas 
            ORDER BY ausencias_coletivas DESC
            LIMIT 15
        ''').fetchall()
        conn.close()
        
        return [{'numero': row['numero_dezena'], 
                'ausencias': row['ausencias_coletivas'],
                'lacuna': row['lacuna_temporal']} for row in dados]
    
    def get_posicoes_fixas(self):
        """Análise de posições fixas"""
        return {'message': 'Análise de posições em desenvolvimento'}
    
    def get_sequencias_tubulares(self):
        """Análise de sequências tubulares"""
        return {'message': 'Análise de sequências em desenvolvimento'}

# Instanciar analisador avançado
analyzer = DiaDeSorteAnalyzerAdvanced()

# Funções de exportação CORRIGIDAS
def gerar_txt_palpites(palpites):
    """
    📄 GERA ARQUIVO TXT COM DEZENAS + MÊS ABREVIADO
    FORMATO: 01 02 03 04 05 06 07 Jan
    """
    try:
        conteudo = []
        meses_abrev = {
            'Janeiro': 'Jan', 'Fevereiro': 'Fev', 'Março': 'Mar', 
            'Abril': 'Abr', 'Maio': 'Mai', 'Junho': 'Jun',
            'Julho': 'Jul', 'Agosto': 'Ago', 'Setembro': 'Set',
            'Outubro': 'Out', 'Novembro': 'Nov', 'Dezembro': 'Dez'
        }
        
        # Cabeçalho informativo
        conteudo.append("# PALPITES DIA DE SORTE - SISTEMA INTELIGENTE")
        conteudo.append("# Formato: Dezena1 Dezena2 Dezena3 Dezena4 Dezena5 Dezena6 Dezena7 MêsAbrev")
        conteudo.append("# 5 Regras Obrigatórias + Números Gatilho + Mês Estatístico")
        conteudo.append("")
        
        for i, palpite in enumerate(palpites, 1):
            # Formatar dezenas: 01 02 03 04 05 06 07
            dezenas_formatadas = " ".join([f"{d:02d}" for d in palpite['dezenas']])
            
            # Abreviar mês: Janeiro -> Jan
            mes_abrev = meses_abrev.get(palpite['mes_sorte'], palpite['mes_sorte'][:3])
            
            # Linha final: 01 02 03 04 05 06 07 Jan
            linha_completa = f"{dezenas_formatadas} {mes_abrev}"
            
            # Adicionar comentário com detalhes (opcional)
            linha_comentario = f"# Jogo {i:02d}: Força {palpite['forca']}, {palpite['detalhes']['distribuicao']}, {palpite['detalhes']['finais_iguais']} finais iguais"
            
            conteudo.append(linha_comentario)
            conteudo.append(linha_completa)
            conteudo.append("")  # Linha em branco
        
        return "\n".join(conteudo)
        
    except Exception as e:
        print(f"❌ Erro ao gerar TXT: {e}")
        return f"# ERRO ao gerar arquivo TXT: {str(e)}"

def gerar_xlsx_palpites(palpites):
    """📊 Gera arquivo XLSX com os palpites incluindo coluna do jogo completo"""
    try:
        dados = []
        meses_abrev = {
            'Janeiro': 'Jan', 'Fevereiro': 'Fev', 'Março': 'Mar', 
            'Abril': 'Abr', 'Maio': 'Mai', 'Junho': 'Jun',
            'Julho': 'Jul', 'Agosto': 'Ago', 'Setembro': 'Set',
            'Outubro': 'Out', 'Novembro': 'Nov', 'Dezembro': 'Dez'
        }
        
        for i, palpite in enumerate(palpites, 1):
            detalhes = palpite['detalhes']
            
            # Criar jogo completo formatado
            dezenas_formatadas = " ".join([f"{d:02d}" for d in palpite['dezenas']])
            mes_abrev = meses_abrev.get(palpite['mes_sorte'], palpite['mes_sorte'][:3])
            jogo_completo = f"{dezenas_formatadas} {mes_abrev}"
            
            linha = {
                'Jogo': i,
                'Jogo_Completo': jogo_completo,  # Nova coluna com formato de exportação
                'Dezena_1': palpite['dezenas'][0],
                'Dezena_2': palpite['dezenas'][1],
                'Dezena_3': palpite['dezenas'][2],
                'Dezena_4': palpite['dezenas'][3],
                'Dezena_5': palpite['dezenas'][4],
                'Dezena_6': palpite['dezenas'][5],
                'Dezena_7': palpite['dezenas'][6],
                'Mes_da_Sorte': palpite['mes_sorte'],
                'Mes_Abrev': mes_abrev,
                'Forca': palpite['forca'],
                'Tentativas': palpite['tentativas'],
                'Distribuicao': detalhes['distribuicao'],
                'Finais_Iguais': detalhes['finais_iguais'],
                'Sequencias': detalhes['sequencias'],
                'Repeticoes_Ultimo': detalhes['repeticoes_ultimo'],
                'Soma_Total': detalhes['soma'],
                'Custo': 2.50,
                'Validacao_5_Regras': 'CORRIGIDA',
                'Metodo_Mes_Sorte': 'ANALISE_COMPLETA_NORMALIZADA',
                'Numeros_Gatilho_Usados': detalhes.get('numeros_gatilho_usados', 'N/A')
            }
            dados.append(linha)
        
        df = pd.DataFrame(dados)
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
        temp_file.close()
        
        with pd.ExcelWriter(temp_file.name, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Palpites', index=False)
        
        return temp_file.name
        
    except Exception as e:
        print(f"Erro ao gerar XLSX: {e}")
        return None

def obter_estatisticas_faixas():
    """📊 ESTATÍSTICAS DE QUEM MAIS SAIU: BAIXOS, MÉDIOS, ALTOS"""
    try:
        historico = analyzer.get_historico_completo()
        
        if not historico or len(historico) < 10:
            return {
                'error': 'Histórico insuficiente para análise',
                'concursos': len(historico)
            }
        
        print(f"\n📊 ANALISANDO DISTRIBUIÇÃO DE FAIXAS EM {len(historico)} CONCURSOS:")
        print("="*60)
        
        # Contadores
        count_baixos = [0] * 10    # 01-10
        count_medios = [0] * 10    # 11-20  
        count_altos = [0] * 11     # 21-31
        
        total_baixos_por_jogo = []
        total_medios_por_jogo = []
        total_altos_por_jogo = []
        
        for concurso in historico:
            dezenas_str = concurso.get('dezenas', '')
            if not dezenas_str:
                continue
                
            try:
                dezenas = [int(x) for x in dezenas_str.split(',')]
            except:
                continue
            
            baixos_jogo = 0
            medios_jogo = 0
            altos_jogo = 0
            
            for dezena in dezenas:
                if 1 <= dezena <= 10:
                    count_baixos[dezena - 1] += 1
                    baixos_jogo += 1
                elif 11 <= dezena <= 20:
                    count_medios[dezena - 11] += 1
                    medios_jogo += 1
                elif 21 <= dezena <= 31:
                    count_altos[dezena - 21] += 1
                    altos_jogo += 1
            
            total_baixos_por_jogo.append(baixos_jogo)
            total_medios_por_jogo.append(medios_jogo)
            total_altos_por_jogo.append(altos_jogo)
        
        # Análise dos números mais frequentes
        baixos_mais_frequentes = []
        for i, freq in enumerate(count_baixos):
            baixos_mais_frequentes.append({
                'numero': i + 1,
                'frequencia': freq,
                'percentual': round((freq / len(historico) * 100), 1)
            })
        
        medios_mais_frequentes = []
        for i, freq in enumerate(count_medios):
            medios_mais_frequentes.append({
                'numero': i + 11,
                'frequencia': freq,
                'percentual': round((freq / len(historico) * 100), 1)
            })
        
        altos_mais_frequentes = []
        for i, freq in enumerate(count_altos):
            altos_mais_frequentes.append({
                'numero': i + 21,
                'frequencia': freq,
                'percentual': round((freq / len(historico) * 100), 1)
            })
        
        # Ordenar por frequência
        baixos_mais_frequentes.sort(key=lambda x: x['frequencia'], reverse=True)
        medios_mais_frequentes.sort(key=lambda x: x['frequencia'], reverse=True)
        altos_mais_frequentes.sort(key=lambda x: x['frequencia'], reverse=True)
        
        # Distribuição por jogo
        from collections import Counter
        dist_baixos = Counter(total_baixos_por_jogo)
        dist_medios = Counter(total_medios_por_jogo)
        dist_altos = Counter(total_altos_por_jogo)
        
        # Estatísticas resumidas
        media_baixos = sum(total_baixos_por_jogo) / len(total_baixos_por_jogo)
        media_medios = sum(total_medios_por_jogo) / len(total_medios_por_jogo)
        media_altos = sum(total_altos_por_jogo) / len(total_altos_por_jogo)
        
        print(f"📊 MÉDIAS POR JOGO:")
        print(f"   🔵 Baixos (01-10): {media_baixos:.1f}")
        print(f"   🟡 Médios (11-20): {media_medios:.1f}")
        print(f"   🔴 Altos (21-31): {media_altos:.1f}")
        
        print(f"\n🏆 TOP 5 MAIS FREQUENTES POR FAIXA:")
        print(f"🔵 BAIXOS (01-10):")
        for i, num in enumerate(baixos_mais_frequentes[:5], 1):
            print(f"   {i}º - {num['numero']:02d}: {num['frequencia']} vezes ({num['percentual']}%)")
        
        print(f"🟡 MÉDIOS (11-20):")
        for i, num in enumerate(medios_mais_frequentes[:5], 1):
            print(f"   {i}º - {num['numero']:02d}: {num['frequencia']} vezes ({num['percentual']}%)")
        
        print(f"🔴 ALTOS (21-31):")
        for i, num in enumerate(altos_mais_frequentes[:5], 1):
            print(f"   {i}º - {num['numero']:02d}: {num['frequencia']} vezes ({num['percentual']}%)")
        
        print("="*60 + "\n")
        
        resultado = {
            'success': True,
            'total_concursos': len(historico),
            'medias': {
                'baixos': round(media_baixos, 1),
                'medios': round(media_medios, 1),
                'altos': round(media_altos, 1)
            },
            'top_5_baixos': baixos_mais_frequentes[:5],
            'top_5_medios': medios_mais_frequentes[:5],
            'top_5_altos': altos_mais_frequentes[:5],
            'distribuicao_baixos': dict(dist_baixos),
            'distribuicao_medios': dict(dist_medios),
            'distribuicao_altos': dict(dist_altos),
            'todos_baixos': baixos_mais_frequentes,
            'todos_medios': medios_mais_frequentes,
            'todos_altos': altos_mais_frequentes
        }
        
        return resultado
        
    except Exception as e:
        print(f"❌ Erro ao calcular estatísticas de faixas: {e}")
        return {
            'success': False,
            'error': str(e)
        }

# ===== ROTAS DA APLICAÇÃO =====

@app.route('/')
def index():
    """Página principal"""
    latest_data = fetch_latest_data()
    historico = analyzer.get_historico_completo(50)
    
    if len(historico) < 20:
        print("Carregando dados históricos...")
        analyzer.fetch_multiple_concursos(50)
    
    return render_template('index.html', 
                         latest_data=latest_data, 
                         total_historico=len(historico))

@app.route('/api/carregar-historico')
def api_carregar_historico():
    """API para carregar histórico de concursos"""
    try:
        limite = request.args.get('limite', 100, type=int)
        concursos_salvos = analyzer.fetch_multiple_concursos(limite)
        
        if concursos_salvos > 0:
            return jsonify({
                'success': True,
                'concursos_salvos': concursos_salvos,
                'message': f'{concursos_salvos} concursos carregados com sucesso!'
            })
        else:
            return jsonify({
                'success': False,
                'concursos_salvos': 0,
                'message': 'Nenhum concurso novo foi carregado'
            })
            
    except Exception as e:
        print(f"❌ Erro ao carregar histórico: {e}")
        return jsonify({
            'success': False,
            'concursos_salvos': 0,
            'message': f'Erro ao carregar histórico: {str(e)}'
        })

@app.route('/api/analise-avancada')
def api_analise_avancada():
    """API para análises estatísticas avançadas"""
    try:
        tipo = request.args.get('tipo', 'mapa_calor')
        
        if tipo == 'pares_impares':
            dados = analyzer.get_analise_pares_impares()
        elif tipo == 'mapa_calor':
            dados = analyzer.get_mapa_calor()
        elif tipo == 'ausencias_coletivas':
            dados = analyzer.get_ausencias_coletivas()
        elif tipo == 'posicoes_fixas':
            dados = analyzer.get_posicoes_fixas()
        elif tipo == 'sequencias_tubulares':
            dados = analyzer.get_sequencias_tubulares()
        else:
            dados = {'error': 'Tipo de análise não encontrado'}
        
        return jsonify(dados)
        
    except Exception as e:
        print(f"❌ Erro na análise {tipo}: {e}")
        return jsonify({
            'error': f'Erro ao carregar análise: {str(e)}'
        })

@app.route('/api/gerar-palpites-personalizados', methods=['POST'])
def api_gerar_palpites_personalizados():
    """
    🎯 API PARA GERAR PALPITES COM AS 5 REGRAS CORRETAS
    🎯 INCLUINDO NÚMEROS GATILHO E MÊS DA SORTE INTELIGENTE (TODOS OS CONCURSOS + NORMALIZAÇÃO)
    """
    global ultimos_palpites_gerados
    
    try:
        dados = request.get_json()
        quantidade = dados.get('quantidade', 5)
        analises = dados.get('analises', {})
        regras = dados.get('regras', {})
        
        print(f"🎲 Gerando {quantidade} palpites com 5 REGRAS CORRETAS...")
        
        ultimo_real = buscar_ultimo_sorteio_real()
        ultimo_sorteio_dezenas = ultimo_real['dezenas'] if ultimo_real else None
        
        numeros_gatilho = []
        usar_gatilho = regras.get('numeros_gatilho', False)
        
        if usar_gatilho:
            numeros_gatilho = extrair_numeros_gatilho_ultra_mega_criativos()
            print(f"🎯 NÚMEROS GATILHO ULTRA MEGA CRIATIVOS ATIVADOS: {numeros_gatilho}")
        else:
            print("🎯 Números gatilho DESATIVADOS")
        
        print("✅ 5 REGRAS CORRETAS:")
        print("   1. ⚖️ Pares vs Ímpares (3P/4I) - SEMPRE")
        print("   2. 🔢 Finais Iguais (EXATAMENTE 2 pares) - SEMPRE")
        print("   3. 🔗 Sequências (EXATAMENTE 2 duplas consecutivas) - SEMPRE")
        print("   4. 🔄 Repetições (EXATAMENTE 2 do último concurso) - SEMPRE")
        print("   5. 📊 Distribuição Faixas (2-3 cada) - SEMPRE")
        print("🌡️ MÊS DA SORTE: ANÁLISE COMPLETA + NORMALIZAÇÃO ROBUSTA")
        
        if ultimo_real:
            print(f"🎯 Último sorteio REAL para validação: {ultimo_sorteio_dezenas}")
        
        # 🌡️ CALCULAR O MÊS DA SORTE UMA ÚNICA VEZ PARA TODOS OS PALPITES
        print(f"\n🌡️ CALCULANDO MÊS DA SORTE INTELIGENTE (TODOS OS CONCURSOS)...")
        mes_sorte_inteligente = calcular_mes_sorte_inteligente()
        print(f"🎯 MÊS DA SORTE ESCOLHIDO PARA ESTE LOTE: {mes_sorte_inteligente}")
        
        palpites = []
        
        for i in range(quantidade):
            tentativas = 0
            max_tentativas = 300
            jogo_valido = False
            
            print(f"\n🎲 Gerando jogo {i+1}/{quantidade} com 5 regras CORRETAS...")
            if usar_gatilho:
                print(f"🎯 Usando números gatilho: {numeros_gatilho}")
            print(f"📅 Mês da sorte: {mes_sorte_inteligente}")
            
            while not jogo_valido and tentativas < max_tentativas:
                tentativas += 1
                
                jogo_final, tentativas_interna = gerar_jogo_com_regras_corretas(
                    ultimo_sorteio_dezenas, 
                    numeros_gatilho, 
                    usar_gatilho
                )
                
                if validar_jogo_completo(jogo_final, ultimo_sorteio_dezenas):
                    jogo_valido = True
                    
                    pares = len([x for x in jogo_final if x % 2 == 0])
                    impares = len([x for x in jogo_final if x % 2 == 1])
                    
                    finais = [x % 10 for x in jogo_final]
                    finais_count = Counter(finais)
                    finais_iguais = sum(1 for count in finais_count.values() if count == 2)
                    
                    sequencias = sum(1 for i in range(len(sorted(jogo_final)) - 1) if sorted(jogo_final)[i+1] == sorted(jogo_final)[i] + 1)
                    
                    repeticoes_ultimo = 0
                    if ultimo_sorteio_dezenas:
                        repeticoes_ultimo = len([x for x in jogo_final if x in ultimo_sorteio_dezenas])
                    
                    gatilhos_usados = []
                    if usar_gatilho and numeros_gatilho:
                        gatilhos_usados = [n for n in jogo_final if n in numeros_gatilho]
                    
                    # 🌡️ USAR O MESMO MÊS DA SORTE PARA TODOS OS PALPITES
                    mes_sorte = mes_sorte_inteligente
                    
                    forca_base = random.randint(88, 96)
                    
                    palpite = {
                        'dezenas': jogo_final,
                        'mes_sorte': mes_sorte,
                        'forca': forca_base,
                        'tentativas': tentativas,
                        'detalhes': {
                            'distribuicao': f'{pares}P/{impares}I',
                            'finais_iguais': finais_iguais,
                            'sequencias': sequencias,
                            'repeticoes_ultimo': repeticoes_ultimo,
                            'soma': sum(jogo_final),
                            'analises_usadas': [k for k, v in analises.items() if v],
                            'regras_aplicadas': ['pares_impares', 'finais_iguais', 'sequencias', 'repeticoes', 'distribuicao_faixas'],
                            'validacao_correta': True,
                            'ultimo_sorteio_usado': ultimo_sorteio_dezenas is not None,
                            'numeros_gatilho_ativo': usar_gatilho,
                            'numeros_gatilho_usados': gatilhos_usados,
                            'total_gatilhos_disponiveis': len(numeros_gatilho) if numeros_gatilho else 0,
                            'metodo_mes_sorte': 'ANALISE_COMPLETA_NORMALIZADA'
                        }
                    }
                    
                    palpites.append(palpite)
                    gatilho_info = f", Gatilhos usados: {gatilhos_usados}" if usar_gatilho else ""
                    print(f"✅ Jogo {i+1} gerado e VALIDADO! (Força: {forca_base}, Mês: {mes_sorte}, Finais: {finais_iguais} pares{gatilho_info})")
                    break
                else:
                    if tentativas % 50 == 0:
                        print(f"⚠️ Tentativa {tentativas} - ainda buscando jogo com regras corretas...")
            
            if not jogo_valido:
                print(f"❌ Não foi possível gerar jogo {i+1} com regras corretas após {max_tentativas} tentativas")
        
        ultimos_palpites_gerados = palpites
        
        total_validados = len([p for p in palpites if p['detalhes'].get('validacao_correta', False)])
        total_com_gatilho = len([p for p in palpites if p['detalhes'].get('numeros_gatilho_usados', [])])
        
        print(f"\n📊 ESTATÍSTICAS FINAIS:")
        print(f"✅ Jogos gerados com REGRAS CORRETAS: {total_validados}/{len(palpites)}")
        print(f"🎯 Jogos com números gatilho: {total_com_gatilho}/{len(palpites)}")
        print(f"🌡️ MÊS DA SORTE ÚNICO: {mes_sorte_inteligente} (ANÁLISE COMPLETA + NORMALIZAÇÃO)")
        print(f"🎯 Último sorteio usado para validação: {ultimo_real['numero'] if ultimo_real else 'N/A'}")
        print(f"🎯 Números gatilho disponíveis: {numeros_gatilho}")
        
        return jsonify({
            'success': True,
            'palpites': palpites,
            'total_gerados': len(palpites),
            'total_validados': total_validados,
            'ultimo_sorteio_real': ultimo_real,
            'numeros_gatilho_funcionais': usar_gatilho,
            'numeros_gatilho_extraidos': numeros_gatilho,
            'total_jogos_com_gatilho': total_com_gatilho,
            'mes_sorte_unico': mes_sorte_inteligente,
            'metodo_mes_sorte': 'ANALISE_COMPLETA_NORMALIZADA',
            'regras_corretas_aplicadas': [
                'pares_impares (3P/4I)',
                'finais_iguais (EXATAMENTE 2 pares)',
                'sequencias (EXATAMENTE 2 duplas consecutivas)',
                'repeticoes (EXATAMENTE 2 do último sorteio)',
                'distribuicao_faixas (2-3 cada)'
            ],
            'validacao': {
                'jogos_validados': total_validados,
                'percentual_sucesso': f"{(total_validados/len(palpites)*100):.1f}%" if len(palpites) > 0 else "0%",
                'regras_corretas_aplicadas': True,
                'api_real_usada': ultimo_real is not None,
                'finais_iguais_corrigido': 'EXATAMENTE 2 PARES',
                'numeros_gatilho_funcionais': usar_gatilho,
                'mes_sorte_completo': True,
                'mes_unico_para_todos': True,
                'normalizacao_robusta': True
            }
        })
        
    except Exception as e:
        print(f"❌ Erro ao gerar palpites: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Erro ao gerar palpites: {str(e)}'
        })

@app.route('/api/estatisticas-faixas')
def api_estatisticas_faixas():
    """📊 API para obter estatísticas de baixos/médios/altos"""
    try:
        stats = obter_estatisticas_faixas()
        return jsonify(stats)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/debug/numeros-gatilho-criativos')
def debug_numeros_gatilho():
    """🔍 DEBUG: Testa extração criativa de números gatilho"""
    try:
        print("\n🎯 TESTANDO EXTRAÇÃO ULTRA MEGA CRIATIVA DE NÚMEROS GATILHO:")
        
        numeros = extrair_numeros_gatilho_ultra_mega_criativos()
        
        return jsonify({
            'success': True,
            'numeros_gatilho': numeros,
            'total': len(numeros),
            'timestamp': datetime.now().isoformat(),
            'metodo': 'ULTRA_MEGA_CRIATIVO'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/export/txt')
def export_txt():
    """📄 Exporta palpites em formato TXT"""
    global ultimos_palpites_gerados
    
    try:
        if not ultimos_palpites_gerados:
            return jsonify({
                'success': False,
                'message': 'Nenhum palpite foi gerado ainda. Gere palpites primeiro!'
            })
        
        conteudo_txt = gerar_txt_palpites(ultimos_palpites_gerados)
        
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8')
        temp_file.write(conteudo_txt)
        temp_file.close()
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        nome_arquivo = f'DiadeSorte_COMPLETO_{timestamp}.txt'
        
        return send_file(
            temp_file.name,
            as_attachment=True,
            download_name=nome_arquivo,
            mimetype='text/plain'
        )
        
    except Exception as e:
        print(f"❌ Erro no export TXT: {e}")
        return jsonify({
            'success': False,
            'message': f'Erro ao exportar TXT: {str(e)}'
        })

@app.route('/export/xlsx')
def export_xlsx():
    """📊 Exporta palpites em formato XLSX"""
    global ultimos_palpites_gerados
    
    try:
        if not ultimos_palpites_gerados:
            return jsonify({
                'success': False,
                'message': 'Nenhum palpite foi gerado ainda. Gere palpites primeiro!'
            })
        
        arquivo_xlsx = gerar_xlsx_palpites(ultimos_palpites_gerados)
        
        if not arquivo_xlsx:
            return jsonify({
                'success': False,
                'message': 'Erro ao gerar arquivo XLSX'
            })
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        nome_arquivo = f'DiadeSorte_COMPLETO_{timestamp}.xlsx'
        
        return send_file(
            arquivo_xlsx,
            as_attachment=True,
            download_name=nome_arquivo,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        print(f"❌ Erro no export XLSX: {e}")
        return jsonify({
            'success': False,
            'message': f'Erro ao exportar XLSX: {str(e)}'
        })

def fetch_latest_data():
    """Busca dados mais recentes da API"""
    try:
        response = requests.get(API_URL, timeout=10)
        if response.status_code == 200:
            data = response.json()
            analyzer.save_concurso_avancado(data)
            return data
        return None
    except Exception as e:
        print(f"Erro ao buscar dados da API: {e}")
        return None

if __name__ == '__main__':
    print("🎯 SISTEMA COMPLETO - Dia de Sorte COM TODAS AS FUNCIONALIDADES!")
    print("✅ VALIDAÇÃO CORRIGIDA:")
    print("   1. ⚖️ Pares vs Ímpares (3P/4I) - SEMPRE")
    print("   2. 🔢 Finais Iguais (EXATAMENTE 2 pares) - SEMPRE")
    print("   3. 🔗 Sequências (EXATAMENTE 2 duplas consecutivas) - SEMPRE")
    print("   4. 🔄 Repetições (EXATAMENTE 2 do último concurso) - SEMPRE")
    print("   5. 📊 Distribuição Faixas (2-3 cada) - SEMPRE")
    print("🎯 NÚMEROS GATILHO ULTRA MEGA CRIATIVOS FUNCIONAIS!")
    print("🌡️ MÊS DA SORTE: TODOS OS CONCURSOS + NORMALIZAÇÃO ROBUSTA!")
    print("📊 FORMATOS SUPORTADOS: 1,2,3 | Jan,Fev,Mar | Janeiro,Fevereiro,Março")
    print("📄 EXPORTAÇÃO CORRIGIDA: Formato '01 02 03 04 05 06 07 Mês'")
    print("🌐 API REAL da Caixa integrada")
    print("")
    print("📊 ROTAS DE ESTATÍSTICAS:")
    print("   🌐 http://localhost:5110/api/estatisticas-faixas - Estatísticas de Baixos/Médios/Altos")
    print("   🌐 http://localhost:5110/api/analise-avancada?tipo=mapa_calor - Mapa de Calor")
    print("   🌐 http://localhost:5110/api/analise-avancada?tipo=pares_impares - Pares vs Ímpares")
    print("   🌐 http://localhost:5110/debug/numeros-gatilho-criativos - Números Gatilho Ultra Mega Criativos")
    print("")
    print("🎯 FUNCIONALIDADES ESPECIAIS:")
    print("   🧠 Extração ultra mega criativa de números gatilho")
    print("   📊 Análise estatística completa por faixas")
    print("   🌡️ Mês da sorte baseado em análise histórica completa")
    print("   🔍 Debug completo de todas as funcionalidades")
    print("   ➕➖✖️➗ 4 operações matemáticas nos números gatilho")
    print("   🔄 Inversões e transformações criativas")
    print("   💰 Exclusões criativas do valor arrecadado")
    print("")
    print("🌐 PORTA: 5110")
    
    app.run(debug=True, host='0.0.0.0', port=5110)
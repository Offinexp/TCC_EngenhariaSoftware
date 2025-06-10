import pytest
import sys
import os
import statistics
import csv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from factory import db, create_app
from config import TestingConfig
from models import Usuario

tempos_execucao = []
resultados = []
nomes_testes = []

@pytest.fixture
def test_client():
    app = create_app(test_config=TestingConfig)
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()

@pytest.fixture(scope='module')
def init_user():
    app = create_app(test_config=TestingConfig)
    with app.app_context():
        user = Usuario(nome='Administrador4', email='admin4@tcc.com')
        user.set_senha('1234')
        db.session.add(user)
        db.session.commit()
        print("\nUsuário de teste criado: admin4@tcc.com / 1234")
        yield user
        db.session.delete(user)
        db.session.commit()
        print("Usuário de teste removido.")

def registra_dados(nome_teste, tempo, categoria):
    nomes_testes.append(nome_teste)
    tempos_execucao.append(tempo)
    resultados.append(categoria)

def imprime_relatorio():
    if not tempos_execucao:
        print("\nNenhum tempo de execução registrado.")
        return

    media = statistics.mean(tempos_execucao)
    desvio = statistics.stdev(tempos_execucao) if len(tempos_execucao) > 1 else 0
    coef_var = desvio / media if media != 0 else 0

    print("\n📊 Análise Quantitativa dos Tempos de Execução dos Testes:")
    print(f"- Média de tempo: {media:.4f} segundos")
    print(f"- Desvio padrão: {desvio:.4f} segundos")
    print(f"- Coeficiente de variação: {coef_var:.4f}")

    frequencias = {}
    total = len(resultados)
    for r in resultados:
        frequencias[r] = frequencias.get(r, 0) + 1

    print("\n📈 Frequências dos Resultados (categorias):")
    for cat, freq_abs in frequencias.items():
        freq_rel = freq_abs / total if total > 0 else 0
        print(f"- {cat}: Frequência absoluta = {freq_abs}, Frequência relativa = {freq_rel:.2%}")

def salva_csv(nome_arquivo='relatorio_testes.csv'):
    with open(nome_arquivo, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Nome do Teste', 'Tempo de Execução (s)', 'Resultado'])
        for nome, tempo, resultado in zip(nomes_testes, tempos_execucao, resultados):
            writer.writerow([nome, f"{tempo:.4f}", resultado])
    print(f"\n💾 Relatório CSV salvo em: {nome_arquivo}")

def executa_teste(test_client, payload_email, payload_senha, nome_teste, benchmark):
    def call_post():
        return test_client.post('/login', data={
            'email': payload_email,
            'senha': payload_senha
        }, follow_redirects=True)

    response = benchmark(call_post)
    tempo_exec = benchmark.stats['mean']

    if 'Credenciais inválidas' in response.data.decode('utf-8'):
        resultado = "Bloqueado"
    else:
        resultado = "Não Bloqueado"

    with test_client.application.app_context():
        # Verifica se o usuário com email igual ao payload está gravado no banco
        usuario_no_banco = Usuario.query.filter_by(email=payload_email).first()

    registra_dados(nome_teste, tempo_exec, resultado)

    print(f"\n🔹 {nome_teste}")
    print(f"Payload: email='{payload_email}', senha='{payload_senha}'")
    print(f"Tempo de execução (média): {tempo_exec:.4f} segundos")
    print(f"Resultado: {resultado}")
    print(f"Usuário no banco: {'Sim' if usuario_no_banco else 'Não'}")

    # Assertiva que injeções foram bloqueadas e nenhum usuário foi gravado no banco
    assert resultado == "Bloqueado", "Teste falhou: injeção SQL não foi bloqueada"
    assert usuario_no_banco is None, "Falha: Usuário malicioso foi gravado no banco"
    print("✅ Teste passou.")

def test_login_sql_injection(test_client, init_user, benchmark):
    executa_teste(test_client, "' OR '1'='1", "' OR '1'='1", "SQL Injection OR '1'='1'", benchmark)

def test_login_sql_injection_drop_table(test_client, init_user, benchmark):
    executa_teste(test_client, "'; DROP TABLE usuario; --", "qualquer", "SQL Injection DROP TABLE", benchmark)
    try:
        usuarios = Usuario.query.all()
        print(f"✅ Tabela 'usuario' continua existente. Total de usuários: {len(usuarios)}")
    except Exception as e:
        pytest.fail(f"❌ ERRO: Tabela 'usuario' pode ter sido removida! {e}")

def test_login_sql_injection_comment(test_client, init_user, benchmark):
    executa_teste(test_client, "' OR 1=1 --", "qualquer", "SQL Injection comentário --", benchmark)

# @pytest.mark.order(after='test_login_sql_injection_comment')
# def test_analise_quantitativa_final():
#     imprime_relatorio()
#     salva_csv()
#     assert True

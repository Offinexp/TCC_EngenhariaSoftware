import pytest
import sys
import os
import statistics
import csv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from factory import db, create_app
from config import TestingConfig
from models import Usuario, Produto, Categoria

# Listas para armazenar dados do benchmark
tempos_execucao = []
resultados = []
nomes_testes = []

@pytest.fixture(scope='module')
def app():
    app = create_app(test_config=TestingConfig)
    with app.app_context():
        db.create_all()
        print("\n✅ Banco de dados criado para os testes de produtos.")
        yield app
        db.session.remove()
        db.drop_all()
        print("🧹 Banco de dados limpo após os testes de produtos.")

@pytest.fixture(scope='module')
def test_client(app):
    return app.test_client()

@pytest.fixture(scope='module')
def init_user(app):
    with app.app_context():
        user = Usuario(nome='Administrador2', email='admin2@tcc.com', nivel_acesso='admin')
        user.set_senha('1234')
        db.session.add(user)
        db.session.commit()
        print("\n👤 Usuário administrador criado para testes.")
        yield user
        db.session.delete(user)
        db.session.commit()
        print("🧹 Usuário administrador removido após testes.")

@pytest.fixture(scope='module')
def categoria_existente(app):
    with app.app_context():
        categoria = Categoria(nome='Categoria Teste')
        db.session.add(categoria)
        db.session.commit()
        print("\n📂 Categoria criada para teste.")
        yield categoria
        db.session.delete(categoria)
        db.session.commit()
        print("🧹 Categoria removida após teste.")

@pytest.fixture(scope='module')
def authenticated_client(test_client, init_user):
    print("\n🔐 Efetuando login do usuário administrador para testes...")
    login_response = test_client.post('/login', data={
        'email': init_user.email,
        'senha': '1234'
    }, follow_redirects=True)
    assert login_response.status_code == 200
    print("✅ Login realizado com sucesso.")
    return test_client

# Função para registrar dados do benchmark
def registra_dados(nome_teste, tempo, categoria):
    nomes_testes.append(nome_teste)
    tempos_execucao.append(tempo)
    resultados.append(categoria)

# Função que executa o post com benchmark e valida o resultado - Confere no banco tamb
def executa_teste_produto(client, app, payload_nome, categoria_id, nome_teste, benchmark):
    def call_post():
        return client.post('/admin/produtos/novo', data={
            'nome': payload_nome,
            'descricao': 'Descrição segura',
            'quantidade': '10',
            'preco': '100.00',
            'categoria': str(categoria_id)
        }, follow_redirects=True)

    response = benchmark(call_post)
    tempo_exec = benchmark.stats['mean']

    print(f"\n🔎 {nome_teste}")
    print(f"Status code da resposta: {response.status_code}")

    html_text = response.data.decode('utf-8')

    # Verifica se o payload aparece na resposta HTTP
    if payload_nome in html_text:
        resultado = "Falha"
        print(f"❌ {nome_teste}: Payload malicioso foi exibido na resposta! Vulnerabilidade detectada.")
    else:
        resultado = "Bloqueado"
        print(f"✅ {nome_teste}: Payload malicioso NÃO foi exibido na resposta. Teste passou.")

    # Verifica se o payload foi gravado no banco de dados
    with app.app_context():
        registro = Produto.query.filter_by(nome=payload_nome).first()
        if registro:
            resultado = "Falha"
            print(f"❌ {nome_teste}: Payload malicioso FOI gravado no banco! Vulnerabilidade detectada.")
        else:
            print(f"✅ {nome_teste}: Payload malicioso NÃO foi gravado no banco.")

    registra_dados(nome_teste, tempo_exec, resultado)

    print(f"Payload: {payload_nome}")
    print(f"Tempo médio de execução: {tempo_exec:.4f} segundos")
    print(f"Resultado: {resultado}")

    assert resultado == "Bloqueado"

# Agora, todos os testes passam o parâmetro app também
def test_injecao_sql_com_aspas_benchmark(authenticated_client, categoria_existente, app, benchmark):
    executa_teste_produto(authenticated_client,
                          app,
                          "'; DROP TABLE produtos; --",
                          categoria_existente.id,
                          "Injeção SQL com aspas",
                          benchmark)

def test_injecao_sql_sem_aspas_benchmark(authenticated_client, categoria_existente, app, benchmark):
    executa_teste_produto(authenticated_client,
                          app,
                          "1; DROP TABLE produtos;",
                          categoria_existente.id,
                          "Injeção SQL sem aspas",
                          benchmark)

def test_injecao_sql_com_comment_benchmark(authenticated_client, categoria_existente, app, benchmark):
    executa_teste_produto(authenticated_client,
                          app,
                          "' OR 1=1 --",
                          categoria_existente.id,
                          "Injeção SQL com comentário --",
                          benchmark)

def test_tabela_produtos_nao_excluida(authenticated_client, app):
    print("\n🔍 Verificação: tabela produtos intacta")
    with app.app_context():
        try:
            produtos = Produto.query.all()
            print(f"✅ Tabela produtos está intacta. Total de produtos: {len(produtos)}")
            assert produtos is not None
        except Exception as e:
            pytest.fail(f"❌ Tabela produtos foi alterada ou excluída: {e}")

def imprime_relatorio():
    if not tempos_execucao:
        print("\n⚠️ Nenhum tempo registrado.")
        return

    media = statistics.mean(tempos_execucao)
    desvio = statistics.stdev(tempos_execucao) if len(tempos_execucao) > 1 else 0
    coef_var = desvio / media if media != 0 else 0

    print("\n📊 Análise Quantitativa dos Tempos:")
    print(f"- Média: {media:.4f} s")
    print(f"- Desvio padrão: {desvio:.4f} s")
    print(f"- Coeficiente de variação: {coef_var:.4f}")

    frequencias = {}
    total = len(resultados)
    for r in resultados:
        frequencias[r] = frequencias.get(r, 0) + 1

    print("\n📈 Frequências dos Resultados:")
    for cat, freq_abs in frequencias.items():
        freq_rel = freq_abs / total if total > 0 else 0
        print(f"- {cat}: absoluta = {freq_abs}, relativa = {freq_rel:.2%}")

def salva_csv(nome_arquivo='relatorio_produtos.csv'):
    with open(nome_arquivo, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Nome do Teste', 'Tempo (s)', 'Resultado'])
        for nome, tempo, res in zip(nomes_testes, tempos_execucao, resultados):
            writer.writerow([nome, f"{tempo:.4f}", res])
    print(f"\n💾 CSV salvo: {nome_arquivo}")

# Para gerar relatório ao final dos testes, você pode descomentar e chamar manualmente se preferir:
# def test_relatorio_final_produtos():
#     imprime_relatorio()
#     salva_csv()
#     assert True

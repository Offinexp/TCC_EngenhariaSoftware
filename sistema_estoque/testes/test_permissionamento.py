# import pytest
# import sys
# import os
# import statistics
# import csv

# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# from factory import create_app, db
# from config import TestingConfig
# from models import Usuario

# # Listas para armazenar dados do benchmark
# tempos_execucao = []
# resultados = []
# nomes_testes = []

# @pytest.fixture(scope='module')
# def app():
#     app = create_app(test_config=TestingConfig)
#     with app.app_context():
#         db.create_all()
#         yield app
#         db.session.remove()
#         db.drop_all()

# @pytest.fixture
# def client(app):
#     return app.test_client()

# #Usuário comum

# @pytest.fixture
# def usuario_comum(app):
#     with app.app_context():
#         usuario = Usuario(nome='Usuário Comum 1', email='usuario1@tcc.com', nivel_acesso='usuario')
#         usuario.set_senha('1234')
#         db.session.add(usuario)
#         db.session.commit()
#         yield usuario
#         db.session.delete(usuario)
#         db.session.commit()

# #Usuário Admin

# @pytest.fixture
# def usuario_admin(app):
#     with app.app_context():
#         admin = Usuario(nome='Administrador 1', email='admin1@tcc.com', nivel_acesso='admin')
#         admin.set_senha('1234')
#         db.session.add(admin)
#         db.session.commit()
#         yield admin
#         db.session.delete(admin)
#         db.session.commit()

# def login(client, email, senha):
#     return client.post('/login', data={'email': email, 'senha': senha}, follow_redirects=True)

# def logout(client):
#     return client.get('/logout', follow_redirects=True)

# def registra_dados(nome_teste, tempo, resultado):
#     nomes_testes.append(nome_teste)
#     tempos_execucao.append(tempo)
#     resultados.append(resultado)

# #Validar se o usuário admin consegue acessar /admin - Deve dar Sucesso
# def test_admin_pode_acessar_admin_dashboard(client, usuario_admin, benchmark):
#     login(client, usuario_admin.email, '1234')

#     def acao():
#         return client.get('/admin')
    
#     response = benchmark(acao)
#     tempo_exec = benchmark.stats['mean']
#     logout(client)

#     resultado = "Sucesso" if response.status_code == 200 and b'Painel Admin' in response.data else "Falha"
#     registra_dados("Admin pode acessar dashboard", tempo_exec, resultado)
#     print(f"\n🔹 Admin dashboard acesso - Tempo: {tempo_exec:.4f}s - Resultado: {resultado}")
#     assert resultado == "Sucesso"

# #Validar se o usuário comum consegue acessar o /admin - Este deve falhar
# def test_usuario_comum_nao_pode_acessar_admin_dashboard(client, usuario_comum, benchmark):
#     login(client, usuario_comum.email, '1234')

#     def acao():
#         return client.get('/admin', follow_redirects=True)
    
#     response = benchmark(acao)
#     tempo_exec = benchmark.stats['mean']
#     logout(client)

#     resultado = "Sucesso" if b'Painel Admin' not in response.data and b'Bem-vindo' in response.data else "Falha"
#     registra_dados("Usuário comum não pode acessar admin", tempo_exec, resultado)
#     print(f"\n🔹 Usuário comum acesso admin negado - Tempo: {tempo_exec:.4f}s - Resultado: {resultado}")
#     assert resultado == "Sucesso"

# #Validar se qualquer um consegue acessar /admin
# def test_nao_autenticado_nao_pode_acessar_admin(client, benchmark):
#     def acao():
#         return client.get('/admin', follow_redirects=True)
    
#     response = benchmark(acao)
#     tempo_exec = benchmark.stats['mean']

#     resultado = "Sucesso" if b'Login' in response.data else "Falha"
#     registra_dados("Não autenticado não pode acessar admin", tempo_exec, resultado)
#     print(f"\n🔹 Não autenticado acesso admin negado - Tempo: {tempo_exec:.4f}s - Resultado: {resultado}")
#     assert resultado == "Sucesso"

# #Validar se usuário admin pode criar produto - Deve dar Sucesso
# def test_admin_pode_criar_produto(client, usuario_admin, benchmark):
#     login(client, usuario_admin.email, '1234')

#     def acao():
#         return client.post('/admin/produtos/novo', data={
#             'nome': 'Produto Teste',
#             'quantidade_em_estoque': 10,
#             'preco': '50.00',
#             'categoria_id': 1
#         }, follow_redirects=True)
    
#     response = benchmark(acao)
#     tempo_exec = benchmark.stats['mean']
#     logout(client)

#     resultado = "Sucesso" if (b'Produto Teste' in response.data or response.status_code == 200) else "Falha"
#     registra_dados("Admin pode criar produto", tempo_exec, resultado)
#     print(f"\n🔹 Admin cria produto - Tempo: {tempo_exec:.4f}s - Resultado: {resultado}")
#     assert resultado == "Sucesso"

# #Validar se usuário comum consegue criar produto - Deve falhar
# def test_usuario_comum_nao_pode_criar_produto(client, usuario_comum, benchmark):
#     login(client, usuario_comum.email, '1234')

#     def acao():
#         return client.post('/admin/produtos/novo', data={
#             'nome': 'Produto Teste',
#             'quantidade_em_estoque': 10,
#             'preco': '50.00',
#             'categoria_id': 1
#         }, follow_redirects=True)
    
#     response = benchmark(acao)
#     tempo_exec = benchmark.stats['mean']
#     logout(client)

#     resposta_texto = response.data.decode('utf-8')
#     resultado = "Sucesso" if ('Permissão negada' in resposta_texto or 'Bem-vindo' in resposta_texto) else "Falha"
#     registra_dados("Usuário comum não pode criar produto", tempo_exec, resultado)
#     print(f"\n🔹 Usuário comum cria produto negado - Tempo: {tempo_exec:.4f}s - Resultado: {resultado}")
#     assert resultado == "Sucesso"


# def test_logout_bloqueia_acesso(client, usuario_admin, benchmark):
#     # Primeiro faz login e logout para garantir que a sessão está encerrada
#     login(client, usuario_admin.email, '1234')
#     logout(client)

#     # Benchmarka apenas a tentativa de acesso após logout
#     def acao():
#         return client.get('/admin', follow_redirects=True)
    
#     response = benchmark(acao)
#     tempo_exec = benchmark.stats['mean']

#     resultado = "Sucesso" if b'Login' in response.data else "Falha"
#     registra_dados("Logout bloqueia acesso admin", tempo_exec, resultado)
#     print(f"\n🔹 Logout bloqueia acesso admin - Tempo: {tempo_exec:.4f}s - Resultado: {resultado}")
#     assert resultado == "Sucesso"
    
# def imprime_relatorio():
#     if not tempos_execucao:
#         print("\n⚠️ Nenhum tempo registrado.")
#         return

#     media = statistics.mean(tempos_execucao)
#     desvio = statistics.stdev(tempos_execucao) if len(tempos_execucao) > 1 else 0
#     coef_var = desvio / media if media != 0 else 0

#     print("\n📊 Análise Quantitativa dos Tempos:")
#     print(f"- Média: {media:.4f} s")
#     print(f"- Desvio padrão: {desvio:.4f} s")
#     print(f"- Coeficiente de variação: {coef_var:.4f}")

#     frequencias = {}
#     total = len(resultados)
#     for r in resultados:
#         frequencias[r] = frequencias.get(r, 0) + 1

#     print("\n📈 Frequências dos Resultados:")
#     for cat, freq_abs in frequencias.items():
#         freq_rel = freq_abs / total if total > 0 else 0
#         print(f"- {cat}: absoluta = {freq_abs}, relativa = {freq_rel:.2%}")

# def salva_csv(nome_arquivo='relatorio_usuarios.csv'):
#     with open(nome_arquivo, mode='w', newline='', encoding='utf-8') as file:
#         writer = csv.writer(file)
#         writer.writerow(['Nome do Teste', 'Tempo (s)', 'Resultado'])
#         for nome, tempo, res in zip(nomes_testes, tempos_execucao, resultados):
#             writer.writerow([nome, f"{tempo:.4f}", res])
#     print(f"\n💾 CSV salvo: {nome_arquivo}")

# @pytest.mark.order(after='test_logout_bloqueia_acesso')
# def test_relatorio_final_usuarios():
#     imprime_relatorio()
#     salva_csv()
#     assert True

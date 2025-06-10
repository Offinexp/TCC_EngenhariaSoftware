from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, Response
from flask_login import login_user, login_required, logout_user, current_user
from factory import db
from models import Usuario, Categoria, Produto
import csv
from io import StringIO

main = Blueprint('main', __name__)

@main.errorhandler(403)
def erro_403(e):
    return render_template('403.html'), 403

@main.route('/')
def index():
    return redirect(url_for('main.login'))

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        print(">>> Entrou no login POST")
        try:
            email = request.form['email']
            senha = request.form['senha']
            print(f"    ↓ Dados recebidos: {email} / {senha}")

            usuario = Usuario.query.filter_by(email=email).first()
            print("    ↓ Query.filter_by retornou:", usuario)

            if usuario:
                if usuario.verificar_senha(senha):
                    print("    ✔ Senha correta — efetuando login")
                    login_user(usuario)
                    return redirect(url_for('main.dashboard'))
                else:
                    print("    ✖ Senha incorreta")
            else:
                print("    ✖ Usuário não encontrado")

            flash('Credenciais inválidas!', 'danger')
        except Exception as e:
            print("!!! Exceção no login:", e)
            flash('Erro interno — veja o console', 'danger')
    return render_template('login.html')

@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))

@main.route('/dashboard')
@login_required
def dashboard():
    if current_user.nivel_acesso == 'admin':
        return redirect(url_for('main.admin_dashboard'))
    return render_template('dashboard.html')

@main.route('/admin')
@login_required
def admin_dashboard():
    if current_user.nivel_acesso != 'admin':
        abort(403)
    produtos = Produto.query.all()
    return render_template('admin_dashboard.html', produtos=produtos)

@main.route('/admin/produtos/novo', methods=['GET', 'POST'])
@login_required
def novo_produto():
    if current_user.nivel_acesso != 'admin':
        abort(403)

    categorias = Categoria.query.all()

    if request.method == 'POST':
        nome = request.form['nome']
        descricao = request.form['descricao']
        quantidade = int(request.form['quantidade'])
        preco = float(request.form['preco'])
        categoria_id = int(request.form['categoria'])

        novo = Produto(
            nome=nome,
            descricao=descricao,
            quantidade_em_estoque=quantidade,
            preco=preco,
            categoria_id=categoria_id
        )
        db.session.add(novo)
        db.session.commit()
        flash('Produto cadastrado com sucesso!', 'success')
        return redirect(url_for('main.admin_dashboard'))

    return render_template('novo_produto.html', categorias=categorias)

@main.route('/exportar_estoque')
@login_required
def exportar_estoque():
    produtos = Produto.query.all()

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Nome', 'Descrição', 'Qtd. Estoque', 'Preço', 'Categoria'])

    for produto in produtos:
        writer.writerow([
            produto.nome,
            produto.descricao,
            produto.quantidade_em_estoque,
            f"{produto.preco:.2f}",
            produto.categoria.nome if produto.categoria else ''
        ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment;filename=estoque.csv'}
    )

@main.route('/admin/produtos/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_produto(id):
    if current_user.nivel_acesso != 'admin':
        abort(403)

    produto = Produto.query.get_or_404(id)
    categorias = Categoria.query.all()

    if request.method == 'POST':
        produto.nome = request.form['nome']
        produto.descricao = request.form['descricao']
        produto.quantidade_em_estoque = int(request.form['quantidade'])
        produto.preco = float(request.form['preco'])
        produto.categoria_id = int(request.form['categoria'])

        db.session.commit()
        flash('Produto atualizado com sucesso!', 'success')
        return redirect(url_for('main.admin_dashboard'))

    return render_template('editar_produto.html', produto=produto, categorias=categorias)

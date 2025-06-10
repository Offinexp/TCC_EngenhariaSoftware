from app import app
from factory import db
from models import Usuario
from werkzeug.security import generate_password_hash


with app.app_context():
    usuarios = Usuario.query.all()
    for usuario in usuarios:
        nova_senha = '1234'
        usuario.senha = generate_password_hash(nova_senha)
    db.session.commit()
    print("Senhas atualizadas para o hash do Werkzeug!")

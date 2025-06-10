class Config:
    SECRET_KEY = 'minha_chave_super_secreta_para_desenvolvimento'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = (
        'mysql+mysqlconnector://root:12583214@127.0.0.1/estoque_db?connect_timeout=5'
    )
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_timeout': 5,
    }

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'  # banco isolado e volátil
    SQLALCHEMY_ENGINE_OPTIONS = {}

from sqlalchemy import create_engine

uri = 'mysql+mysqlconnector://root:12583214@localhost/estoque_db?connect_timeout=5'
engine = create_engine(uri)

try:
    with engine.connect() as conn:
        print("✅ Conectou com sucesso ao MySQL!")
except Exception as e:
    print("❌ Falha ao conectar:", e)

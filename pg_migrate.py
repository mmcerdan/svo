from app import create_app
from app.extensions import db

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        conn.execute(db.text("ALTER TABLE obitos ADD COLUMN IF NOT EXISTS causas_morte_cids JSONB DEFAULT '[]'"))
        conn.execute(db.text("ALTER TABLE obitos ADD COLUMN IF NOT EXISTS estabelecimento_id INTEGER REFERENCES estabelecimentos(id)"))
        conn.commit()
        print('Migration done!')
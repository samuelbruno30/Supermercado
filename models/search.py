from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from db import db

class SearchQuery(db.Model):
    __tablename__ = 'search_queries'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    raw_query: Mapped[str] = mapped_column(db.Text, nullable=False)
    sanitized: Mapped[str] = mapped_column(db.Text)
    results_json: Mapped[str] = mapped_column(db.Text)         # armazenar json.dumps(dados)
    
    # 👇 CORRIGIDO AQUI!
    user_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow, index=True)
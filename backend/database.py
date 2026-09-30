from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()



def normalizar_database_url(url: str) -> str:
    """Heroku, Render, Railway, Fly etc. entregam 'postgres://...'; o SQLAlchemy 2 só aceita 'postgresql://'."""
    url = url.strip()
    if url.startswith("postgres://"):
        return "postgresql://" + url[len("postgres://"):]
    return url


DATABASE_URL = normalizar_database_url(
    os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/stock")
)

# SQLite (desenvolvimento local sem Postgres): FastAPI usa threadpool, então
# a conexão precisa poder ser usada fora da thread que a criou.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

# pool_pre_ping: bancos gerenciados derrubam conexões ociosas; testa antes de usar.
engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

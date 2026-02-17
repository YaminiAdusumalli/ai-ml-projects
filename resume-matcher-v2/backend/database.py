from sqlalchemy import create_engine, Column, Integer, String, Text, Float
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from sqlalchemy.orm import declarative_base, sessionmaker
from pathlib import Path

# ---- Create a data folder for DB ----
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ---- SQLite DB file path ----
DB_PATH = DATA_DIR / "resume_matcher.db"
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

# ---- Engine + Session ----
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# ---- Tables ----
class Resume(Base):
    __tablename__ = "resumes"
    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(String, unique=True, index=True)
    filename = Column(String)
    content_json = Column(SQLiteJSON)  # parsed resume data


class MatchResult(Base):
    __tablename__ = "matches"
    id = Column(Integer, primary_key=True, index=True)
    job_description = Column(Text)
    resume_id = Column(String, index=True)
    score = Column(Float)
    skills_score = Column(Float)
    experience_score = Column(Float)
    education_score = Column(Float)
    fit_label = Column(String)


def init_db():
    Base.metadata.create_all(bind=engine)

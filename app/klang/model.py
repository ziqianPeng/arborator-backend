from sqlalchemy import BLOB, Boolean, Column, Integer, String, Boolean, TEXT
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy_utils import ChoiceType

from app import db  # noqa

class Transcription(db.Model):
    __tablename__ = "Klang"
    id = Column(Integer, primary_key=True)
    user = Column(String(100), nullable=False)
    mp3 = Column(String(100), nullable=False)
    sound = Column(String(20), nullable=False)
    story = Column(String(20), nullable=False)
    accent = Column(String(20), nullable=False)
    monodia = Column(String(20), nullable=False)
    title = Column(String(20), nullable=False)
    transcription = Column(TEXT)

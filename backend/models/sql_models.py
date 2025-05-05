from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class ResearchProject(Base):
    __tablename__ = 'research_projects'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class ResearchDocument(Base):
    __tablename__ = 'research_document'

    id = Column(String, primary_key=True, index=True)
    project_id = Column(Integer, index=True)
    text = Column(String, nullable=False)
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    
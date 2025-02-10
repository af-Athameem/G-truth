from sqlalchemy import create_engine, Column, INTEGER, UUID, String, ForeignKey, TIMESTAMP, Text
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
import uuid
# from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
#from database import Base

# Database connection
DATABASE_URL = "postgresql://neondb_owner:npg_Pf3SdCBQpA8q@ep-winter-grass-a563m20i-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class TestCase(Base):
    __tablename__ = "testcase"

    test_case_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question = Column(Text, nullable=False)
    ideal_answer = Column(Text, nullable=False)
    agent_name = Column(String(255), nullable=False)
    created_on = Column(TIMESTAMP, default=datetime.utcnow)

    tags = relationship("TestCaseHasTag", back_populates="test_case")
    documents = relationship("TestCaseRefersToDocument", back_populates="test_case")


class Tag(Base):
    __tablename__ = "tag"

    tag_name = Column(String(255), primary_key=True)


class Document(Base):
    __tablename__ = "document"

    name = Column(String(255), primary_key=True)
    company = Column(String(255), nullable=True)


class TestCaseHasTag(Base):
    __tablename__ = "testcasehastag"

    test_case_id = Column(UUID(as_uuid=True), ForeignKey("testcase.test_case_id"), primary_key=True)
    tag_name = Column(String(255), ForeignKey("tag.tag_name"), primary_key=True)

    test_case = relationship("TestCase", back_populates="tags")
    tag = relationship("Tag")


class TestCaseRefersToDocument(Base):
    __tablename__ = "testcasereferstodocument"

    test_case_id = Column(UUID(as_uuid=True), ForeignKey("testcase.test_case_id"), primary_key=True)
    document_name = Column(String(255), ForeignKey("document.name"), primary_key=True)
    pages = Column(Text, nullable=False)

    test_case = relationship("TestCase", back_populates="documents")
    document = relationship("Document")


class Users(Base):
    __tablename__ = "users"

    id = Column(INTEGER, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)  # Store hashed password

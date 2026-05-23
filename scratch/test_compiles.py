import sys
import sqlalchemy as sa
from sqlalchemy import create_engine, Column, Integer, String, Computed
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import declarative_base

try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    class Vector:
        pass

from sqlalchemy.dialects.postgresql import TSVECTOR, UUID, JSONB

# Compiles rules for SQLite
@compiles(Vector, "sqlite")
def compile_vector_sqlite(type_, compiler, **kw):
    return "TEXT"

@compiles(TSVECTOR, "sqlite")
def compile_tsvector_sqlite(type_, compiler, **kw):
    return "TEXT"

@compiles(UUID, "sqlite")
def compile_uuid_sqlite(type_, compiler, **kw):
    return "CHAR(36)"

@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(type_, compiler, **kw):
    return "TEXT"

is_sqlite = True  # Mock dialect check

def uuid_type():
    return sa.String(36) if is_sqlite else UUID(as_uuid=True)

def server_default_uuid():
    return None if is_sqlite else sa.text("uuid_generate_v4()")

def json_type():
    return sa.JSON() if is_sqlite else JSONB()

def vector_type():
    return sa.JSON() if is_sqlite else Vector(1536)

def tsv_column_args():
    if is_sqlite:
        return [sa.String(), sa.Computed("coalesce(content, '') || ' ' || coalesce(summary, '')")]
    return [TSVECTOR(), sa.Computed("to_tsvector('english', coalesce(content,'') || ' ' || coalesce(summary,''))", persisted=True)]

Base = declarative_base()

class TestModel(Base):
    __tablename__ = 'test_table'
    id = Column(uuid_type(), primary_key=True, server_default=server_default_uuid())
    content = Column(sa.Text(), nullable=False)
    summary = Column(sa.Text(), nullable=True)
    embedding = Column(vector_type())
    metadata_ = Column(json_type(), nullable=False, server_default="{}")
    
    tsv_args = tsv_column_args()
    tsv = Column(*tsv_args, nullable=True)

# Compile the schema for SQLite
engine = create_engine("sqlite:///:memory:")
try:
    Base.metadata.create_all(engine)
    print("SUCCESS: Tables compiled and created successfully on SQLite with helpers!")
except Exception as e:
    import traceback
    traceback.print_exc()
    sys.exit(1)

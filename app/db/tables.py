from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Table, Column
from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlalchemy import Integer, SmallInteger, String, Date, Float

from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.expression import Insert

from app.consts import ProdType

Base = declarative_base()

class Equity(Base):
    __tablename__ = 'equity'

    prod_id = Column(Integer, unique=True)
    typ = Column(SmallInteger, primary_key=True)
    symbol = Column(String, primary_key=True)
    expiry = Column(Date, primary_key=True)
    strike = Column(Float, primary_key=True)
    opt_typ = Column(SmallInteger, primary_key=True)

    __table_args__ = (
        CheckConstraint('typ in (%d, %d, %d, %d, %d, %d)' % (
            ProdType.index, ProdType.idx_fut, ProdType.idx_opt,
            ProdType.equity, ProdType.eq_fut, ProdType.eq_opt)),
    )

class Debt(Base):
    __tablename__ = 'debt'
    
    prod_id = Column(Integer, unique=True)
    typ = Column(SmallInteger, primary_key=True)
    symbol = Column(String, primary_key=True)
    coupon = Column(Float, primary_key=True)
    maturity = Column(Date, nullable=False)
    issue_date = Column(Date)
    coupon_freq = Column(SmallInteger)

    __table_args__ = (
        UniqueConstraint('typ', 'symbol', 'coupon', 'maturity',
                         'issue_date', 'coupon_freq'),
        CheckConstraint('typ in (%d, %d)' % (
            ProdType.g_sec, ProdType.t_bill)),
    )

class Level(Base):
    __tablename__ = 'levels'
    prod_id = Column(Integer, primary_key=True)
    date = Column(Date, primary_key=True)
    value = Column(Float, nullable=False)
    
@compiles(Insert)
def prefix_inserts(insert, compiler, **kw):
    return compiler.visit_insert(insert.prefix_with("OR IGNORE"), **kw)

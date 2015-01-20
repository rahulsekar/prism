from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

#locals
import tables
from ..config import SQLITE_DB

_engine = None

def _connect():
    global _engine
    _engine = create_engine('sqlite:///%s' % SQLITE_DB)
    tables.Base.metadata.create_all(_engine)
    return sessionmaker(bind=_engine)

session = _connect()()

def max_prod_id():
    return max([
        0,
        session.query(func.max(tables.Equity.prod_id)).first()[0],
        session.query(func.max(tables.Debt.prod_id)).first()[0],
    ])

def prices(date, prod_ids):
    return session.query(tables.Level.value).filter(
        tables.Level.prod_id.in_(prod_ids),
        tables.Level.date == date).all()

def debt_prods(prod_ids=[], typs=[], symbols=[], coupons=[]):
    q = session.query(tables.Debt)

    if len(prod_ids):
        q = q.filter(tables.Debt.prod_id.in_(prod_ids))
    if len(typs):
        q = q.filter(tables.Debt.typ.in_(typs))
    if len(symbols):
        q = q.filter(tables.Debt.symbol.in_(symbols))
    if len(coupons):
        q = q.filter(tables.Debt.coupon.in_(coupons))

    return q.all()

def traded_prods(dates=[], prod_ids=[]):
    q = session.query(tables.Level)
    
    if len(dates):
        q = q.filter(tables.Level.date.in_(dates))
    if len(prod_ids):
        q = q.filter(tables.Level.prod_id.in_(prod_ids))

    return q.all()

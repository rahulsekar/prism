import datetime

#locals
from app import db, consts
import bond, asof

def get_traded_treasury_bonds():
    
    prods = db.utils.debt_prods(
        typs=[consts.ProdType.g_sec,
              consts.ProdType.t_bill])

    traded = [row.prod_id for row in db.utils.traded_prods(
        dates=[asof.date],
        prod_ids=[prod.prod_id for prod in prods])]

    return [bond.Bond(prod) for prod in prods
            if prod.prod_id in traded]

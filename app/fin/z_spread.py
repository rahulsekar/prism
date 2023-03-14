import datetime
from app.fin import disc_curve, bonddata
import pandas as pd


def calculate(dt: datetime.date):
    gsecs, asof_date = bonddata.get_gsec_securities(dt)
    dc = disc_curve.NelsonSiegel(gsecs)

    secs, asof_date = bonddata.get_corp_securities(dt)
    data = []
    for sec in secs:
        p = sec.bond
        dp = sec.dirty_price()
        ytm = sec.ytm()
        zs = sec.zs(dc)
        zs = int(zs*10000) if zs is not None else None
        data.append([p.isin, p.issuer, p.coupon_pct, p.maturity_date, sec.price, dp, ytm, zs, sec.volume, sec.avg_price, p.face_value, p.is_taxable])

    df = pd.DataFrame(data, columns=["isin", "iss", "cpn", "mat", "prc", 'dp', "ytm", "zs", "vol", "avg_price", "fv", 'tax'])
    return df
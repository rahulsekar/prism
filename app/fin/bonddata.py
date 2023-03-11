import datetime

from app.detls import harmoney, ccil, nseindia
from app.fin.base import Security


def get_bonds(isins: list, default_issue_date: datetime.date = datetime.date.today()):
    return harmoney.get_bonds(isins, default_issue_date)
    # return nseindia.get_gsec_bonds(isins)


def get_gsec_securities(asof_date: datetime.date = None):
    mkt_df, asof_date = ccil.get_gsec_mktdata_ccil(asof_date)
    if mkt_df is None or len(mkt_df) < 1:
        return None, None
    ret = []
    bnds = get_bonds(mkt_df['isin'].tolist(), asof_date - datetime.timedelta(days=1))
    for bnd in bnds:
        if not bnd.isin.startswith('IN00'):
            continue
        row = mkt_df[mkt_df['isin'] == bnd.isin]
        if len(row) > 0:
            r = row.iloc[0]
            ret.append(Security(bnd, r.prc, asof_date, r.vol_cr * 1e7 / bnd.face_value, r.avg_prc))
    return ret, asof_date
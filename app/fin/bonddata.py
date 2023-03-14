import datetime

from app.detls import harmoney, ccil, nseindia, bseindia
from app.fin.bond import BondSecurity


def get_bonds(isins: list, default_issue_date: datetime.date = datetime.date.today()):
    return harmoney.get_bonds(isins, default_issue_date)
    # return nseindia.get_gsec_bonds(isins)


def _make_securities(mkt_df, asof_date, isin_prefix=None):
    if mkt_df is None or len(mkt_df) < 1:
        return None, None
    ret = []
    bnds = get_bonds(mkt_df['isin'].tolist(), asof_date - datetime.timedelta(days=1))
    for bnd in bnds:
        if isin_prefix is not None and not bnd.isin.startswith(isin_prefix):
            continue
        row = mkt_df[mkt_df['isin'] == bnd.isin]
        if len(row) > 0:
            r = row.iloc[0]
            ttv = r.vol_cr * 1e7 / bnd.face_value if 'vol_cr' in r else (r.ttv if 'ttv' in r else 0)
            avg_prc = r.avg_prc if 'avg_prc' in r else r.prc
            ret.append(BondSecurity(bnd, r.prc, asof_date, ttv, avg_prc))
    return ret, asof_date


def get_gsec_securities(asof_date: datetime.date = None):
    mkt_df, asof_date = ccil.get_gsec_mktdata_ccil(asof_date)
    return _make_securities(mkt_df, asof_date, isin_prefix='IN00')


def get_corp_securities(asof_date: datetime.date = None):
    mkt_df, asof_date = bseindia.get_corp_bonds_mktdata_bhavcopy(asof_date)
    return _make_securities(mkt_df, asof_date)
import io, datetime
from app.detls import store
from app.fin import bond
import pandas as pd


def _get_raw_data(obj: str, isins: list = None):
    data, ctype = store.get_from_storage(obj)
    df = pd.read_csv(io.BytesIO(data))
    if isins is not None:
        df = df[df['isin'].isin(isins)]
    return df


def _make_dt(x):
    return datetime.datetime.strptime(x, '%Y-%m-%d').date() if not pd.isnull(x) else None


def get_bonds(isins: list) -> list:
    gsec_df = _get_raw_data("harmoney.in/gsec_202303111330.csv", isins)
    corp_df = _get_raw_data("harmoney.in/corp_202303121338_2.csv", isins)
    all_df = pd.concat([corp_df, gsec_df])
    ret = []
    for idx, bnd in all_df.iterrows():
        ret.append(bond.Bond((bnd.coupon if not pd.isnull(bnd.coupon) else 0)*100,
                             _make_dt(bnd.maturity_date),
                             _make_dt(bnd.issue_date),
                             bnd.coupon_frequency if not pd.isnull(bnd.coupon_frequency) else None,
                             face_value=bnd.face_value,
                             isin=bnd['isin'],
                             issuer=bnd.issuer,
                             is_callable=bnd.is_callable if not pd.isnull(bnd.is_callable) else False,
                             is_perpetual=bnd.is_perpetual if not pd.isnull(bnd.is_perpetual) else False,
                             is_taxable = bnd.is_taxable if not pd.isnull(bnd.is_taxable) else True,
                             call_date= _make_dt(bnd.call_date) if not pd.isnull(bnd.call_date) else None
                             ))

    return ret

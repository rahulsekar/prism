import datetime
import io

import pandas as pd
import requests

from app.detls import store
from app.fin import bond


def get_gsec_bonds(isins:list, refresh_storage=False):
    csv_content = None
    obj = "archives.nseindia.com/DEBT.csv"
    if not refresh_storage:
        csv_content, ctype = store.get_from_storage(obj)
    if not csv_content:
        res = requests.get('https://archives.nseindia.com/content/equities/DEBT.csv')
        store.push_to_storage(obj, res.content, res.headers['content-type'])

    clean_csv = csv_content.decode('utf-8').replace(' ', '').replace('INTERESTPAYMENTDT', 'INTERESTPAYMENTDT,ISIN')
    info_df = pd.read_csv(io.StringIO(clean_csv), index_col=False)
    filtered_df = info_df[info_df['ISIN'].isin(isins)].copy()

    filtered_df['IPRATE'] = filtered_df['IPRATE'].fillna(0)
    # print(filtered_df[['SYMBOL', 'FACEVALUE', 'IPRATE', 'MATURITY', 'ISSUEDATE']])
    ret = []
    for idx, bnd in filtered_df.iterrows():
        # print(bnd[1])
        ret.append(bond.Bond(bnd.IPRATE, _pdate(bnd.REDEMPTIONDATE), _pdate(bnd.DATEOFLISTING), 2 if bnd.IPRATE > 0 else 0, face_value=bnd.FACEVALUE, symbol=bnd.SYMBOL, isin=bnd.ISIN))
    return ret


def _pdate(v):
    return datetime.datetime.strptime(v, '%d-%b-%Y').date()

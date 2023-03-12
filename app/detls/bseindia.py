import datetime
import zipfile
from io import BytesIO

import pandas as pd
import requests

from app.detls import store

def _process_bhavcopy_zip(zip_content: bytes, asof_date: datetime.date):
    dt = asof_date.strftime('%d%m%Y')
    zf = zipfile.ZipFile(BytesIO(zip_content))
    fgroup_csv = zf.read("fgroup{}.csv".format(dt))
    icdm_csv = zf.read("icdm{}.csv".format(dt))
    f_df = pd.read_csv(BytesIO(fgroup_csv), on_bad_lines="skip")
    f_df.columns = ['sec_cd', 'sec_name', 'opn_prc', 'high_prc', 'low_prc', 'prc', 'ttv', 'num_trds', 'tt', 'isin',
                    'face_value', 'cpn', 'mat']
    f_df = f_df[['isin', 'prc', 'ttv', 'face_value', 'mat', 'cpn']]
    i_df = pd.read_csv(BytesIO(icdm_csv), on_bad_lines="skip")
    i_df.columns = ['sec_cd', 'sec_name', 'cpn', 'mat', 'prc', 'avg_prc', 'avg_yld', 'tt', 'isin', 'face_value']
    i_df['ttv'] = i_df.apply(lambda x: x.tt * 1e5 / x.face_value, axis=1)
    i_df = i_df[['isin', 'prc', 'ttv', 'face_value', 'mat', 'cpn']]

    return pd.concat([f_df, i_df])


def get_corp_bonds_mktdata_bhavcopy(asof_date: datetime.date, refresh_storage=False):
    obj = 'bseindia.com/DEBTBHAVCOPY{}.zip'.format(asof_date.strftime('%d%m%Y'))
    if not refresh_storage:
        zip_content, ctype = store.get_from_storage(obj)
        if not zip_content:
            return get_corp_bonds_mktdata_bhavcopy(asof_date, True)
    else:
        url = "https://www.bseindia.com/download/Bhavcopy/Debt/DEBTBHAVCOPY{}.zip".format(asof_date.strftime('%d%m%Y'))
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'}
        res = requests.get(url, headers=headers)
        zip_content = res.content
        if res.headers['content-type'] != 'application/x-zip-compressed':
            return None, None
        store.push_to_storage(obj, zip_content, res.headers['content-type'])

    return _process_bhavcopy_zip(zip_content, asof_date), asof_date

def push_corp_bonds_mktdata_to_storage(start_dt: datetime.date, end_dt: datetime.date):
    dt = start_dt
    while dt <= end_dt:
        mkt_df, asof_date = get_corp_bonds_mktdata_bhavcopy(dt)
        if mkt_df is not None:
            print(asof_date, len(mkt_df), end=". ")
        dt += datetime.timedelta(days=1)


def get_traded_corp_isins_from_store(start_dt: datetime.date, end_dt: datetime.date) -> set:
    asof_date = start_dt
    ret = set()
    while asof_date <= end_dt:
        obj = 'bseindia.com/DEBTBHAVCOPY{}.zip'.format(asof_date.strftime('%d%m%Y'))
        data, ctype = store.get_from_storage(obj)
        if data is not None:
            df = _process_bhavcopy_zip(data, asof_date)
            ret = ret.union(set(df['isin'].tolist()))
        asof_date += datetime.timedelta(days=1)
    return ret

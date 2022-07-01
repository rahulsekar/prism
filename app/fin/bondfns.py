import requests
import pandas as pd
from io import StringIO
import datetime

#locals
from bond import Bond
from base import Security


def get_gsec_mktdata():
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'}
    r1 = requests.get('https://www.nseindia.com', headers = headers)
    resp = requests.get('https://www.nseindia.com/api/liveBonds-traded-on-cm',
                      params = {'type': 'gsec'}, headers = headers, cookies = r1.cookies)
    # print(resp.status_code)
    raw = resp.json()['data']
    # print(raw[0])
    filtered = [(x['symbol'], x['faceValue'], x['series'], x['lastPrice']) for x in raw]
    df = pd.DataFrame(filtered, columns= ['sym', 'ser', 'fv', 'prc'])
    return df


def add_info(row):
    dt = datetime.datetime.strptime(row.REDEMPTIONDATE, '%d-%b-%Y').date()
    dol = datetime.datetime.strptime(row.DATEOFLISTING, '%d-%b-%Y').date()
    return pd.Series([dt, dol])


def get_gsec_info():
    resp = requests.get('https://archives.nseindia.com/content/equities/DEBT.csv')
    info_df = pd.read_csv(StringIO(resp.text.replace(' ', '')), index_col=False)
    filtered_df = info_df[info_df['SERIES'].isin(['GS', 'TB'])]
    filtered_df = filtered_df.copy()
    filtered_df[['MATURITY', 'ISSUEDATE']] = filtered_df.apply(add_info, axis=1)
    filtered_df['IPRATE'] = filtered_df['IPRATE'].fillna(0)
    # print(filtered_df[['SYMBOL', 'FACEVALUE', 'IPRATE', 'MATURITY', 'ISSUEDATE']])
    return filtered_df


def get_gsec_bonds():
    df = get_gsec_info()
    ret = []
    for idx, bnd in df.iterrows():
        # print(bnd[1])
        ret.append(Bond(bnd.IPRATE, bnd.MATURITY, bnd.ISSUEDATE, 2 if bnd.IPRATE > 0 else 0, face_value=bnd.FACEVALUE, symbol=bnd.SYMBOL))
    return ret


def get_gsec_securities():
    bnds = get_gsec_bonds()
    mkt_df = get_gsec_mktdata()
    ret = []
    for bnd in bnds:
        row = mkt_df[mkt_df.sym == bnd.symbol]
        if len(row) > 0:
            # print(row.iloc[0].prc)
            ret.append(Security(bnd, row.iloc[0].prc, datetime.date.today()))
    return ret

# mkt_df = get_gsec_mktdata()
# print(mkt_df)
# info_df = get_gsec_info()
# print(info_df)
# bnds = get_gsec_bonds()
# print(len(bnds))
# secs = get_gsec_securities()
# print(len(secs))

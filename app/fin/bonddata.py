import numpy as np
import pandas as pd
from io import StringIO, BytesIO
import re, zipfile, requests, datetime

#locals
from app.fin.bond import Bond
from app.fin.base import Security


def get_gsec_mktdata_nse(use_prev_close: bool = False):
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'}
    r1 = requests.get('https://www.nseindia.com', headers = headers)
    resp = requests.get('https://www.nseindia.com/api/liveBonds-traded-on-cm',
                      params = {'type': 'gsec'}, headers = headers, cookies = r1.cookies)
    # print(resp.status_code)
    raw = resp.json()['data']
    # print(raw[0])
    filtered = [(x['symbol'],
                 x['faceValue'],
                 x['series'],
                 x['lastPrice'] or (x['previousClose'] if use_prev_close else 0),
                 x['totalTradedVolume'],
                 x['averagePrice'],
                 x['buyPrice1'],
                 x['sellPrice1']
                ) for x in raw]
    df = pd.DataFrame(filtered, columns= ['sym', 'ser', 'fv', 'prc', 'vol', 'avg_prc', 'bid', 'ask'])
    return df

def get_gsec_mktdata_ccil():
    res = requests.get("https://www.ccilindia.com/Research/Statistics/Pages/Infovendors.aspx")
    zip_url = re.findall(
        'https://www\.ccilindia\.com/Research/Statistics/Lists/DailyDataForInfoVendors/Attachments/\d+/DFIV_\w+\.zip',
        res.text)[0]
    res = requests.get(zip_url)
    zf = zipfile.ZipFile(BytesIO(res.content))
    outright_csv = zf.read([x for x in zf.namelist() if x.startswith('outright')][0])
    df = pd.read_csv(BytesIO(outright_csv))
    red_df = df[['ISIN', 'Volume (Cr.)', 'Last price', 'Wtd Avg Price']]
    red_df.columns = ['isin', 'vol_cr', 'prc', 'avg_prc']
    red_df['bid']= np.nan
    red_df['ask'] = np.nan
    return red_df

def add_info(row):
    dt = datetime.datetime.strptime(row.REDEMPTIONDATE, '%d-%b-%Y').date()
    dol = datetime.datetime.strptime(row.DATEOFLISTING, '%d-%b-%Y').date()
    return pd.Series([dt, dol])


def get_gsec_info():
    resp = requests.get('https://archives.nseindia.com/content/equities/DEBT.csv')
    clean_csv = resp.text.replace(' ', '').replace('INTERESTPAYMENTDT', 'INTERESTPAYMENTDT,ISIN')
    info_df = pd.read_csv(StringIO(clean_csv), index_col=False)
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
        ret.append(Bond(bnd.IPRATE, bnd.MATURITY, bnd.ISSUEDATE, 2 if bnd.IPRATE > 0 else 0, face_value=bnd.FACEVALUE, symbol=bnd.SYMBOL, isin=bnd.ISIN))
    return ret


def get_gsec_securities():
    bnds = get_gsec_bonds()
    mkt_df = get_gsec_mktdata_ccil()
    ret = []
    for bnd in bnds:
        row = mkt_df[mkt_df['isin'] == bnd.isin]
        if len(row) > 0:
            r = row.iloc[0]
            ret.append(Security(bnd, r.prc, datetime.date.today(), r.vol_cr * 1e7 / bnd.face_value, r.avg_prc, r.bid, r.ask))
    return ret

# mkt_df = get_gsec_mktdata_ccil()
# print(mkt_df)
# info_df = get_gsec_info()
# print(info_df)
# bnds = get_gsec_bonds()
# print(len(bnds))
# gsecs = get_gsec_securities()
# print(len(gsecs))
# data = []
# for gsec in gsecs:
#   p = gsec.product
#   data.append([p.symbol, p.coupon_pct, p.maturity_date, gsec.price, p.yield_to_maturity(gsec.price)])
# df = pd.DataFrame(data, columns=["sym", "cpn", "mat", "prc", "ytm"])
# print(df)

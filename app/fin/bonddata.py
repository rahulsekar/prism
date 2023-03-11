import pandas as pd
from io import StringIO, BytesIO
import re, zipfile, requests, datetime

from app.detls import store, harmoney, nseindia
#locals
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


def _get_gsec_mktdata_ccil_latest():
    res = requests.get("https://www.ccilindia.com/Research/Statistics/Pages/Infovendors.aspx")
    zip_url = re.findall(
        'https://www\.ccilindia\.com/Research/Statistics/Lists/DailyDataForInfoVendors/Attachments/\d+/DFIV_\w+\.zip',
        res.text)[0]
    grps = re.search("DFIV_(\d{2})_(\d{2})_(\d{4})\.zip", zip_url)
    asof_date = datetime.date(int(grps.groups()[2]), int(grps.groups()[1]), int(grps.groups()[0]))
    res = requests.get(zip_url)
    zip_content = res.content
    obj = 'ccilindia.com/DFIV_{}.zip'.format(asof_date.strftime("%d%m%Y"))
    store.push_to_storage(obj, zip_content, res.headers['content-type'])
    return zip_content, asof_date


def _process_ccil_dfiv_zip(zip_content: bytes):
    zf = zipfile.ZipFile(BytesIO(zip_content))
    filenames = [x for x in zf.namelist() if x.startswith('outright')]
    if len(filenames) == 0:
        return None
    outright_csv = zf.read(filenames[0])
    df = pd.read_csv(BytesIO(outright_csv))
    df.drop(df.columns.difference(['ISIN', 'Volume (Cr.)', 'Last price', 'Wtd Avg Price']),
            axis=1, inplace=True)
    df.columns = ['isin', 'vol_cr', 'prc', 'avg_prc']
    return df


def get_gsec_mktdata_ccil(asof_date: datetime.date = None):
    if asof_date is None:
        zip_content, asof_date = _get_gsec_mktdata_ccil_latest()
        return _process_ccil_dfiv_zip(zip_content), asof_date

    obj = 'ccilindia.com/NDSOM_{}.csv'.format(asof_date.strftime("%d%m%Y"))
    csv_content, ctype = store.get_from_storage(obj)
    if csv_content:
        return pd.read_csv(BytesIO(csv_content)), asof_date

    obj = 'ccilindia.com/DFIV_{}.zip'.format(asof_date.strftime("%d%m%Y"))
    zip_content, ctype = store.get_from_storage(obj)
    if not zip_content:
        return None, None
    return _process_ccil_dfiv_zip(zip_content), asof_date


def get_corp_bonds_mktdata_bhavcopy(asof_date: datetime.date, refresh_storage=False):
    dt = asof_date.strftime('%d%m%Y')
    obj = 'bseindia.com/DEBTBHAVCOPY{}.zip'.format(dt)
    if not refresh_storage:
        zip_content, ctype = store.get_from_storage(obj)
        if not zip_content:
            return get_corp_bonds_mktdata_bhavcopy(asof_date, True)
    else:
        url = "https://www.bseindia.com/download/Bhavcopy/Debt/DEBTBHAVCOPY{}.zip".format(dt)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'}
        res = requests.get(url, headers=headers)
        zip_content = res.content
        if res.headers['content-type'] != 'application/x-zip-compressed':
            return None, None
        store.push_to_storage(obj, zip_content, res.headers['content-type'])

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

    return pd.concat([f_df, i_df]), asof_date


def push_corp_bonds_mktdata_to_storage(start_dt: datetime.date, end_dt: datetime.date):
    dt = start_dt
    while dt <= end_dt:
        mkt_df, asof_date = get_corp_bonds_mktdata_bhavcopy(dt)
        if mkt_df is not None:
            print(asof_date, len(mkt_df), end=". ")
        dt += datetime.timedelta(days=1)


def get_bonds(isins: list, default_issue_date: datetime.date = datetime.date.today()):
    return harmoney.get_bonds(isins, default_issue_date)
    # return nseindia.get_gsec_bonds(isins)


def get_gsec_securities(asof_date: datetime.date = None):
    mkt_df, asof_date = get_gsec_mktdata_ccil(asof_date)
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

# mkt_df = get_gsec_mktdata_ccil()
# print(mkt_df)
# info_df =  get_gsec_info()
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

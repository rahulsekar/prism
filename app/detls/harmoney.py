import requests, io, json, datetime
from app.detls import store
from app.fin import bonddata, bond

from google.cloud import storage
import pandas as pd
import numpy as np


def fetch_store_isins(s: set):
    raw_data = {}
    cnt = 0
    for i in s:
        cnt += 1
        print(i, cnt , end=" ")
        res = requests.post('https://api.harmoney.in/api/client-finstrument-list/', json={'category_values': {'finstrument_type': 'Bond', 'keyword_string':'{}'.format(i)}})
        if len(res.json()['results']):
            raw_data[i] = res.json()['results'][0]
            raw_data[i]['search_string'] = ''
        else:
            print("NA", end=" ")
        if cnt % 200 == 0:
            print('\nWriting_to_storage\n')
            store.push_to_storage('harmoney.in/raw_data_{}_{}.json'.format(int(datetime.datetime.now().timestamp() * 1000), cnt), json.dumps(raw_data).encode('utf-8'), 'application/json')
            raw_data = {}
    if cnt % 200 != 0:
        store.push_to_storage('harmoney.in/raw_data_{}_{}.json'.format(int(datetime.datetime.now().timestamp() * 1000), cnt), json.dumps(raw_data).encode('utf-8'), 'application/json')


def get_traded_gsecs(start_dt: datetime.date, end_dt: datetime.date):
    s = set()
    dt = start_dt
    while dt < datetime.date(2023, 4, 30):
        df, asof_date = bonddata.get_gsec_mktdata_ccil(dt)
        if df is not None:
            s = s.union(set(df['isin'].tolist()))
        print(dt, len(s), end=" ")
        dt += datetime.timedelta(days=1)

    return s


def transform_load_isins(prefix="harmoney.in/raw_data"):
    bkt = storage.Client.create_anonymous_client().bucket('prism_data')
    ls = bkt.list_blobs(prefix=prefix)
    df_arr = []
    for b in ls:
        print(b.name)
        isins = json.loads(b.download_as_bytes().decode('utf-8'))
        for i, data in isins.items():
            cp = data['contract_parameters']
            iss_dt = cp.get('start_date',None)
            cfs = cp['coupon_frequency']
            if cfs == 'H':
                cf = 2
            elif cfs == 'Y':
                cf = 1
            elif cfs == 'O' or cfs is None:
                cf = 0
            else:
                raise Exception ('Unkown Coupon Frequency: {}'.format(cfs))
            df_arr.append([i, cp.get('coupon', 0), cf, cp['face_value'],
                           datetime.datetime.fromisoformat(cp['maturity_date']).date(),
                           datetime.datetime.fromisoformat(iss_dt).date() if iss_dt is not None else None,
                           data['issuer']['name']])

    df = pd.DataFrame(df_arr, columns=['isin', 'coupon', 'coupon_frequency', 'face_value', 'maturity_date',  'issue_date', 'issuer'])
    store.push_to_storage('harmoney.in/gsecs_info_{}.csv'.format(datetime.datetime.now().timestamp()), df.to_csv(index=False).encode('utf-8'), 'text/csv')


def get_bonds(isins: list, default_issue_date: datetime.date = datetime.date.today()) -> list:
    data, ctype = store.get_from_storage("harmoney.in/gsecs_info_1678545669.681393.csv")
    df = pd.read_csv(io.StringIO(data.decode("utf-8")), parse_dates=['maturity_date', 'issue_date'])
    df = df[df['isin'].isin(isins)]

    ret = []
    for idx, bnd in df.iterrows():
        ret.append(bond.Bond((bnd.coupon if not pd.isnull(bnd.coupon) else 0)*100,
                             bnd.maturity_date.date(),
                             bnd.issue_date.date() if not pd.isnull(bnd.issue_date) else default_issue_date,
                             bnd.coupon_frequency,
                             face_value=bnd.face_value,
                             isin=bnd['isin'],
                             issuer=bnd.issuer))

    return ret
# s = get_traded_gsecs(datetime.date(2022,4,4), datetime.date(2023,4, 30))
# fetch_store_isins(s)
# transform_load_isins('harmoney.in/raw_data')
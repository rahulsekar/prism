import requests, io, json, datetime

import app.detls.ccil
from app.detls import store
from app.fin import bond

from google.cloud import storage
import pandas as pd


def fetch_store_isins(s: set, batch_id: str):
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
            store.push_to_storage(
                'harmoney.in/{}/{}_{}.json'.format(batch_id, cnt, int(datetime.datetime.now().timestamp() * 1000)),
                json.dumps(raw_data).encode('utf-8'),
                'application/json'
            )
            raw_data = {}
    if cnt % 200 != 0:
        store.push_to_storage(
            'harmoney.in/{}/{}_{}.json'.format(batch_id, cnt, int(datetime.datetime.now().timestamp() * 1000)),
            json.dumps(raw_data).encode('utf-8'),
            'application/json'
        )


def get_traded_gsecs(start_dt: datetime.date, end_dt: datetime.date):
    s = set()
    dt = start_dt
    while dt < end_dt:
        df, asof_date = app.detls.ccil.get_gsec_mktdata_ccil(dt)
        if df is not None:
            s = s.union(set(df['isin'].tolist()))
        print(dt, len(s), end=" ")
        dt += datetime.timedelta(days=1)

    return s


def transform_load_isins(batch_id):
    bkt = storage.Client.create_anonymous_client().bucket('prism_data')
    ls = bkt.list_blobs(prefix="harmoney.in/{}".format(batch_id))
    df_arr = []
    for b in ls:
        print(b.name)
        isins = json.loads(b.download_as_bytes().decode('utf-8'))
        for i, data in isins.items():
            cp = data['contract_parameters']

            cfs = cp.get('coupon_frequency', 'O')
            if cfs == 'M':
                cf = 1
            elif cfs == 'Q':
                cf = 4
            elif cfs == 'H':
                cf = 2
            elif cfs == 'Y':
                cf = 1
            elif cfs == 'O' or cfs is None:
                cf = 0
            else:
                raise Exception ('Unkown Coupon Frequency: {}'.format(cfs))

            m_dt = cp.get('maturity_date', None)
            iss_dt = cp.get('start_date', None)
            c_dt = cp.get('call_date', None)
            df_arr.append([i, cp.get('coupon', 0), cf, cp['face_value'],
                           datetime.datetime.fromisoformat(m_dt).date() if m_dt is not None else None,
                           datetime.datetime.fromisoformat(iss_dt).date() if iss_dt is not None else None,
                           datetime.datetime.fromisoformat(c_dt).date() if c_dt is not None else None,
                           cp.get('is_perpetual', False),
                           cp.get('is_callable', False),
                           data['issuer']['name']])

    df = pd.DataFrame(df_arr, columns=['isin', 'coupon', 'coupon_frequency', 'face_value',
                                       'maturity_date',  'issue_date', 'call_date',
                                       'is_perpetual', 'is_callable', 'issuer'])
    store.push_to_storage(
        'harmoney.in/{}.csv'.format(batch_id),
        df.to_csv(index=False).encode('utf-8'),
        'text/csv'
    )


def _get_raw_data(obj: str, isins: list = None):
    data, ctype = store.get_from_storage(obj)
    df = pd.read_csv(io.BytesIO(data))
    if isins is not None:
        df = df[df['isin'].isin(isins)]
    return df


def _make_dt(x):
    return datetime.datetime.strptime(x, '%Y-%m-%d').date() if not pd.isnull(x) else None


def get_bonds(isins: list, default_issue_date: datetime.date = datetime.date.today()) -> list:
    gsec_df = _get_raw_data("harmoney.in/gsec_202303111330.csv", isins)
    corp_df = _get_raw_data("harmoney.in/corp_202303121338.csv", isins)
    all_df = pd.concat([corp_df, gsec_df])
    ret = []
    for idx, bnd in all_df.iterrows():
        ret.append(bond.Bond((bnd.coupon if not pd.isnull(bnd.coupon) else 0)*100,
                             _make_dt(bnd.maturity_date),
                             _make_dt(bnd.issue_date),
                             bnd.coupon_frequency,
                             face_value=bnd.face_value,
                             isin=bnd['isin'],
                             issuer=bnd.issuer,
                             is_callable=bnd.is_callable if not pd.isnull(bnd.is_callable) else False,
                             is_perpetual=bnd.is_perpetual if not pd.isnull(bnd.is_perpetual) else False,
                             call_date= _make_dt(bnd.call_date) if not pd.isnull(bnd.call_date) else None
                             ))

    return ret
# s = get_traded_gsecs(datetime.date(2022,4,4), datetime.date(2023,4, 30))
# fetch_store_isins(s)
# transform_load_isins('harmoney.in/raw_data')
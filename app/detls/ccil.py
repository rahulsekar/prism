import datetime
import re
import zipfile
from io import BytesIO

import numpy as np
import pandas as pd
import requests

from app.detls import store
from app.detls.store import push_to_storage


# Get file from here: https://tradehist.ccilindia.com/
# push_ccil_ndsom_to_storage(".../Archival_NDSOM_01-Apr-2022_08-Mar-2023.csv", datetime.date(2022,4,4), datetime.date(2023,3,6))
def push_ccil_ndsom_to_storage(filename:str, start_dt:datetime.date, end_dt:datetime.date):
    df = pd.read_csv(filename)
    dt = start_dt
    while(dt <= end_dt):
        dt_df = df[df["Trade Date"] == dt.strftime("%d-%b-%y").upper()].copy()
        if len(dt_df) > 0:
            dt_df["avg_prc"] = dt_df["Trade Price"] * dt_df["Face Value"] / 1e7
            dt_df["vol_cr"] = dt_df["Face Value"] / 1e7
            pt_dt_df = pd.pivot_table(dt_df, index=["ISIN"],
                                         aggfunc={"Trade Date": "last", "Trade Price": "last", "avg_prc": np.sum, "vol_cr": np.sum})
            pt_dt_df["avg_prc"] /= pt_dt_df["vol_cr"]
            pt_dt_df = pt_dt_df.reset_index()
            pt_dt_df.rename(columns={"Trade Price": "prc", "ISIN": "isin", "Trade Date": "trd_dt"}, inplace=True)
            push_to_storage("ccilindia.com/NDSOM_{}.csv".format(dt.strftime("%d%m%Y")), pt_dt_df.to_csv(index=False).encode("utf-8"), "text/csv")
            print("Done {}".format(dt), end=". ")
        dt += datetime.timedelta(days=1)


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

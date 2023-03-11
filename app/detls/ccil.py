import datetime
import numpy as np
import pandas as pd

from app.detls.store import push_to_storage


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

# Get file from here: https://tradehist.ccilindia.com/
# push_ccil_ndsom_to_storage("~/Desktop/Archival_NDSOM_01-Apr-2022_08-Mar-2023.csv", datetime.date(2022,4,4), datetime.date(2023,3,6))

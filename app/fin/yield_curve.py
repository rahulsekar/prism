import pandas as pd
import datetime
from dateutil import relativedelta as rd
from matplotlib import pyplot as plt
#locals
from app.fin import bonddata, disc_curve

def generate():
    gsecs = bondfns.get_gsec_securities()
    # print(len(gsecs))
    data = []
    for gsec in gsecs:
        p = gsec.product
        data.append([p.symbol, p.coupon_pct, p.maturity_date, gsec.price, p.yield_to_maturity(gsec.price)])
    df = pd.DataFrame(data, columns=["sym", "cpn", "mat", "prc", "ytm"])
    print(df)
    filtered_gsecs = [gsec for gsec in gsecs if gsec.product.is_price_sane(gsec.price)]
    dc = disc_curve.NelsonSiegel(filtered_gsecs)

    days = [1, 30, 91, 182, 365, 365 * 3, 365 * 5, 365 * 10, 365 * 20, 365 * 30, 365 * 40]
    rts = [dc.yld(datetime.date.today() + rd.relativedelta(days=d)) * 100 for d in days]
    plt.plot([datetime.date.today() + rd.relativedelta(days=d) for d in days], rts)
    fil_df = df[(0.04 < df.ytm) & (df.ytm < .10)]
    plt.scatter(fil_df.mat, fil_df.ytm * 100)
    plt.xlabel('date')
    plt.ylabel('yield')
    plt.show()

generate()

from app.fin import bonddata
from app.fin import disc_curve
from matplotlib import pyplot as plt
from dateutil import relativedelta as rd
import pandas as pd

def plot_yield_curve(dates: list, plot_ytms=False, annotate=False):

  plt.figure(figsize=(30,10))
  plt.rcParams.update({'font.size': 12})
  plt.xlabel('Tenure - Years')
  plt.ylabel('Yield (%)')
  plt.ylim(2.0, 9)
  plt.grid(axis="y")
  plt.title("India Yield Curve", fontsize=40)

  dfs = []
  for dt in dates:
      gsecs, asof_date = bonddata.get_gsec_securities(dt)
      dc = disc_curve.NelsonSiegel(gsecs)
      print(dt, len(gsecs), (dc.b0, dc.b1, dc.b2, dc.tau))
      data = []
      for gsec in gsecs:
        p = gsec.product
        dp = gsec.price + gsec.product.accrued_interest(gsec.asof_date)
        ytm = p.yield_to_maturity(gsec.price + gsec.product.accrued_interest(gsec.asof_date), asof_date)
        ns_prc = p.npv(dc, gsec.asof_date)
        data.append(
          [dt, p.isin, p.symbol, p.coupon_pct, p.maturity_date, gsec.price, ytm, gsec.volume, gsec.avg_price, p.face_value,
           dp, p.issue_date, ns_prc, ns_prc - gsec.price])

      yrs = [0.33, 0.5, 1, 3, 5, 10, 20, 30, 40]
      rts = [dc.yld(asof_date + rd.relativedelta(days=int(y*365)))*100 for y in yrs]
      plt.plot(yrs, rts, marker="^", label=dt)
      df = pd.DataFrame(data,
                        columns=["dt", "isin", "sym", "cpn", "mat", "prc", "ytm", "vol", "avg_price", "fv", "dp", 'isd',
                                 'ns_prc', 'prc_diff']
                        )
      dfs.append(df)

      if plot_ytms:
        plt.scatter(df.mat.apply(lambda x: (x-asof_date).days/365), df.ytm*100)

      if annotate:
        for (i,j) in zip(yrs, rts):
            plt.text(i+0.15, j-0.1, '({0:.1f}, {1:.2f}%)'.format(i, j))
  plt.legend()
  return pd.concat(dfs)

# import datetime
# dates = [
#     datetime.date(2023, 3, 3),
#     # datetime.date(2022, 12, 2),
#     # datetime.date(2022, 9, 5),
#     # datetime.date(2022, 6, 3),
#     # datetime.date(2022, 4, 4)
# ]
# df = plot_yield_curve(dates, plot_ytms=True, annotate=True)
# plt.show()
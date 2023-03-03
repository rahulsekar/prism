from app.fin import bonddata
import datetime
import pandas as pd

gsecs = bonddata.get_gsec_securities()
data = []
asof_date = datetime.date.today()
for gsec in gsecs:
  p = gsec.product
  ytm = p.yield_to_maturity(gsec.price + gsec.product.accrued_interest(gsec.asof_date))
  data.append([p.symbol, p.coupon_pct, p.maturity_date, gsec.price, ytm, gsec.volume, gsec.avg_price])

df = pd.DataFrame(data, columns=["sym", "cpn", "mat", "prc", "ytm", "vol", "avg_price"])
print(df)

from app.fin import disc_curve
dc = disc_curve.NelsonSiegel(gsecs)
[dc.b0, dc.b1, dc.b2, dc.tau]

import datetime, math
from matplotlib import pyplot as plt
from dateutil import relativedelta as rd
tdy = datetime.date.today()
yrs = [0.33, 0.5, 1, 3, 5, 10, 20, 30, 40]
rts = [dc.yld(tdy + rd.relativedelta(days=int(y*365)))*100 for y in yrs]

plt.figure(figsize=(30,10))
plt.plot(yrs, rts, marker="^", color="red")
plt.scatter(df.mat.apply(lambda x: (x-tdy).days/365), df.ytm*100)
plt.xlabel('yrs')
plt.ylabel('yield')
plt.ylim(6.0, 9)
plt.xlim(-1, 35)
for (i,j) in zip(yrs, rts):
  plt.text(i+0.15, j-0.05, '({0:.1f}, {1:.2f}%)'.format(i, j))
plt.show()
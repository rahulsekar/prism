import math, datetime
from matplotlib import pyplot as plt

#locals
from app.config import PLOTS_DIR
import disc_curve, asof, utils, bondfns

def sample_rate(date, DF):
    yrs = (date - asof.date).days / 365.0
    return 100 * (math.pow(DF, -1.0 / yrs) - 1.0)

def generate_yield_curve(date):

    asof.date = date

    sample_dates = [asof.date + datetime.timedelta(days=90*i)
                    for i in range(1, 120)]
    DC = disc_curve.NelsonSiegel(bondfns.get_traded_treasury_bonds())
    sample_rates = [sample_rate(dt, DC.DF(dt))
                    for dt in sample_dates]
    filepath = ('%s/yc_%s.png' % (PLOTS_DIR, asof.date))

    plt.plot(sample_dates, sample_rates)
    plt.ylabel('rate (%)')
    plt.xlabel('term (yrs)')
    plt.savefig(filepath)

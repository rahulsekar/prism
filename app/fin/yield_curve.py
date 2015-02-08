import math, datetime, os, json
from matplotlib import pyplot as plt

#locals
from app.config import PLOTS_DIR, JSON_DIR
import asof, utils, bondfns, disc_curve

def plot(date):
    return '%s/yc_%s.png' % (PLOTS_DIR, date)

def data_file(date):
    return '%s/yc_%s.json' % (JSON_DIR, date)

def sample_rate(date, DF):
    yrs = (date - asof.date).days / 365.0
    return 100 * (math.pow(DF, -1.0 / yrs) - 1.0)

def params_table(dc):
    header = ['b0', 'b1', 'b2', 'tau']
    return {
        'header' : header,
        'rows' : [['%.4f' % dc.b0,
                   '%.4f' % dc.b1,
                   '%.4f' % dc.b2,
                   '%.4f' % dc.tau]]
    }

def model_fit_table(bnds_to_fit, dc):
    header = ['Symbol', 'Coupon', 'Maturity', 'Price', 'Model Price']
    return {
        'header' : header,
        'rows' : [[bnd.prod.symbol,
                   '%.2f' % bnd.prod.coupon,
                   bnd.prod.maturity.__str__(),
                   '%.4f' % bnd.dirty_price,
                   '%.4f' % bnd.NPV(dc)]
                  for bnd in bnds_to_fit]
    }    

def save_plot(dc):
    sample_dates = [asof.date + datetime.timedelta(days=90*i)
                    for i in range(1, 120)]
    sample_rates = [100 * dc.ZCR(dt) for dt in sample_dates]
    plt.clf()
    plt.plot(sample_dates, sample_rates)
    plt.ylabel('rate (%)')
    plt.xlabel('term (yrs)')
    plt.savefig(plot(asof.date))

def generate(date):
    asof.date = date
    bnds_to_fit = bondfns.get_traded_treasury_bonds()
    dc = disc_curve.NelsonSiegel()
    
    save_plot(dc)
    jsondump = json.dumps({
        'params' : params_table(dc),
        'model_fit' : model_fit_table(bnds_to_fit, dc),
    })
    fh = open(data_file(date), 'w')
    fh.write(jsondump)
    fh.close()

def check_generate(date):
    if not os.path.isfile(plot(date)) or\
       not os.path.isfile(data_file(date)):
        generate(date)

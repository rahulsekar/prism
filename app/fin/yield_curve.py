import json, datetime
from dateutil import relativedelta as rd

#locals
import bondfns, disc_curve

def generate():
    bnds_secs = bondfns.get_gsec_securities()
    dc = disc_curve.NelsonSiegel(bnds_secs)

    durs = [rd.relativedelta(days=x) for x in [1, 30, 91, 182, 365, 365*3, 365*5, 365*10]]
    dts = [datetime.date.today() + dur for dur in durs]
    print([(str(dt), dc.yld(dt)) for dt in dts])

generate()

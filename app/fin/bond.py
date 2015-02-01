import datetime, math, json
from scipy import optimize

#locals
from app import db
import utils, disc_curve, asof

class Bond(object):

    def __init__(self, prod):
        self.prod = prod
        self.clean_price = db.utils.prices(asof.date,
                                           [prod.prod_id])[0][0]
        self.dirty_price = self.clean_price +\
                           self.accrued_interest()
        self.ytm = self.yield_to_maturity()

    def to_dict(self):
        return {
            'type' : self.prod.typ,
            'symbol' : self.prod.symbol,
            'coupon' : '%.3f' % self.prod.coupon,
            'maturity' : self.prod.maturity.__str__(),
            'price' : '%.3f' % self.dirty_price,
            'YTM' : '%.3f' % (100 * self.yield_to_maturity()),
            'duration' : '%.2f' % self.modified_duration(),
            }
            
    def cashflows(self):

        mat = self.prod.maturity
        if not self.prod.coupon_freq:
            return {mat:100.0}

        ret = {}
        add = 12 / self.prod.coupon_freq
        nxt = utils.add_months(self.prod.issue_date, add)

        while nxt <= mat:
            if nxt >= asof.date:
                ret[nxt] = self.prod.coupon / self.prod.coupon_freq
            nxt = utils.add_months(nxt, add)

        if mat in ret:
            ret[mat] += 100.0
        else:
            ret[mat] = 100.0

        return ret

    def accrued_interest(self):

        if not self.prod.coupon_freq:
            return 0

        add = 12 / self.prod.coupon_freq
        cur = self.prod.issue_date
        nxt =  utils.add_months(cur, add) 
        while nxt < asof.date:
            cur = nxt
            nxt = utils.add_months(cur, add)

        settle_date = asof.date + datetime.timedelta(days=1)
        return self.prod.coupon / self.prod.coupon_freq *\
            (settle_date- cur).days / (nxt - cur).days

    def NPV(self, DiscCurve):
        ret = 0
        for d, p in self.cashflows().iteritems():
            ret += p * DiscCurve.DF(d)
        return ret

    def yield_to_maturity(self):
        apr = optimize.brentq(
            lambda r: self.NPV(
                disc_curve.ConstDC(r)) / self.dirty_price - 1.0,
            0.0001, # 1bps
            1.0, # 10000bps
        )
        return 2.0 * (math.sqrt(1.0 + apr) - 1.0) # BEY

    def modified_duration(self):
        sar = self.yield_to_maturity() / 2.0 #semi-annual rate
        ret = 0
        for d, p in self.cashflows().iteritems():
            t = (d - asof.date).days / 365.0 #yrs
            ret += t * p / math.pow((1.0 + sar), 2*t)

        ret /= self.dirty_price * (1.0 + sar)

        return ret;
        
    def z_spread(self, yield_curve):
        pass

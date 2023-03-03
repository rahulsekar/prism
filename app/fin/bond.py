import datetime, math
from dateutil.relativedelta import relativedelta
from scipy import optimize

#locals
from app.fin import disc_curve, base


class Bond(base.Product):

    def __init__(self,
                 coupon_pct: float,
                 maturity_date: datetime.date,
                 issue_date: datetime.date,
                 coupon_freq: int = 2,
                 isin: str = None,
                 symbol: str = None,
                 face_value: float = 100.0,
                 ):

        super().__init__(isin)
        self.symbol = symbol
        self.coupon_pct = coupon_pct
        self.maturity_date = maturity_date
        self.issue_date = issue_date
        self.coupon_freq = coupon_freq
        self.face_value = face_value

    def is_price_sane(self, price, asof_date:datetime.date = datetime.date.today(),
                      y_min: float = -0.0001, y_max: float = 0.25) -> bool:
        if not 0.1 < price / self.face_value < 10.0:
            return False
        y1 = self.npv(disc_curve.ConstDC(y_min), asof_date) / price - 1.0
        y2 = self.npv(disc_curve.ConstDC(y_max), asof_date) / price - 1.0
        return y1*y2 < 0.0

    def _coupon_dates(self) -> tuple:
        if not self.coupon_freq:
            return ()
        ret = []
        i = 1
        mnths = int(12 / self.coupon_freq)
        nxt = self.issue_date  - relativedelta(days=1) + relativedelta(months= i * mnths)
        while nxt <= self.maturity_date:
            ret.append(nxt)
            i += 1
            nxt = self.issue_date + relativedelta(months= i * mnths)
        return tuple(ret)

    def cashflows(self) -> dict:
        mat = self.maturity_date
        ret = {mat: self.face_value}
        if not self.coupon_freq:
            return ret
        dts = self._coupon_dates()
        cpn = self.face_value * self.coupon_pct / self.coupon_freq / 100.0
        for dt in dts:
            ret[dt] = ret.get(dt, 0) + cpn
        return ret

    def accrued_interest(self, dt: datetime.date) -> float:
        if not self.coupon_freq or dt <= self.issue_date:
            return 0

        dts = list(self._coupon_dates()) + [self.issue_date]
        mx = max([d for d in dts if d < dt])
        cpn = self.face_value * self.coupon_pct / 100.0 / self.coupon_freq
        prd = 12 / self.coupon_freq * 30
        return cpn * (dt - mx).days / prd

    def npv(self, dc: base.DiscountCurve, asof_date: datetime.date = datetime.date.today()):
        ret = 0
        for d, p in self.cashflows().items():
            if d >= asof_date:
                ret += p * dc.discount_factor(d, asof_date)
        return ret

    def yield_to_maturity(self, dirty_price: float, asof_date: datetime.date = datetime.date.today()):
        if not self.is_price_sane(dirty_price, asof_date, -0.99, 1.00):
            return None
        apr = optimize.brentq(
            lambda r: self.npv(disc_curve.ConstDC(r), asof_date) / dirty_price - 1.0,
            -0.99, # -99%
            1.00, # +100%
        )
        return 2.0 * (math.sqrt(1.0 + apr) - 1.0) # BEY

    def modified_duration(self, dirty_price, asof_date):
        sar = self.yield_to_maturity(dirty_price, asof_date) / 2.0 #semi-annual rate
        ret = 0
        for d, p in self.cashflows().items():
            t = (d - asof_date).days / 365.0 #yrs
            ret += t * p / math.pow((1.0 + sar), 2*t)

        ret /= dirty_price * (1.0 + sar)

        return ret

    def z_spread(self, yield_curve):
        pass


# bnd = Bond(5.5, datetime.date(2025, 8, 31), datetime.date(2020, 8, 31), 2)
# print([str(d) for d in bnd._coupon_dates()])
# # print([bnd.cashflows().items()])
# ai = bnd.accrued_interest(datetime.date(2022, 9, 1))
# print("Acc Int: ", ai)
# print("NPV: ", bnd.npv(disc_curve.ConstDC(bnd.coupon_pct/100.0)))
# print("YTM: ", bnd.yield_to_maturity(bnd.face_value-0.069))
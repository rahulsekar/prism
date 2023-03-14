import datetime, math
from dateutil.relativedelta import relativedelta
from scipy import optimize

#locals
from app.fin import disc_curve, base

_TAXFREE_CPN_ADJUSTMENT = 0.67

class Bond(base.Product):

    def __init__(self,
                 coupon_pct: float,
                 maturity_date: datetime.date,
                 issue_date: datetime.date = None,
                 coupon_freq: int = 2,
                 isin: str = None,
                 symbol: str = None,
                 face_value: float = 100.0,
                 issuer: str = None,
                 is_callable: bool = False,
                 is_perpetual: bool = False,
                 is_taxable: bool = True,
                 call_date: datetime.date = None
                 ):

        super().__init__(isin)
        self.symbol = symbol
        self.coupon_pct = coupon_pct
        self.maturity_date = maturity_date
        self.issue_date = issue_date
        self.coupon_freq = coupon_freq
        self.face_value = face_value
        self.issuer = issuer
        self.is_callable = is_callable
        self.is_perpetual = is_perpetual
        self.is_taxable = is_taxable
        self.call_date = call_date

    def is_price_sane(self, price, asof_date:datetime.date = datetime.date.today(),
                      y_min: float = -0.0001, y_max: float = 0.25) -> bool:
        if not 0.1 < price / self.face_value < 10.0:
            return False
        y1 = self.npv(disc_curve.ConstDC(y_min), asof_date) / price - 1.0
        y2 = self.npv(disc_curve.ConstDC(y_max), asof_date) / price - 1.0
        return y1*y2 < 0.0

    def start_date(self):
        return self.issue_date if self.issue_date is not None else datetime.date(2000, 1, 1)  #urgh!

    def redemption_date(self):
        if self.is_perpetual:
            isd = self.start_date()
            return datetime.date(isd.year + 100, isd.month, isd.day)

        if self.maturity_date is None:
            raise Exception('Maturity unknown for a non-perpetual bond.')

        return self.maturity_date

    def _coupon_dates(self) -> tuple:
        if self.coupon_freq is None or self.coupon_freq == 0:
            return ()
        ret = []
        mnths = int(12 / self.coupon_freq)
        t_dt = prev_dt = self.redemption_date()
        s_dt = self.start_date()
        i = 0
        while prev_dt > s_dt:
            ret.append(prev_dt)
            i += 1
            prev_dt = t_dt - relativedelta(months=i * mnths)

        return tuple(ret)

    def cashflows(self) -> dict:
        mat = self.redemption_date()
        ret = {mat: self.face_value}
        if not self.coupon_freq:
            return ret
        dts = self._coupon_dates()
        cpn = self.face_value * self.coupon_pct / self.coupon_freq / 100.0
        for dt in dts:
            ret[dt] = ret.get(dt, 0) + cpn
        return ret

    def accrued_interest(self, dt: datetime.date) -> float:
        if not self.coupon_freq or dt <= self.start_date():
            return 0

        dts = list(self._coupon_dates()) + [self.start_date()]
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

    def z_spread(self, yield_curve: base.DiscountCurve, dirty_price: float, asof_date: datetime.date):
        zs = optimize.brentq(
            lambda r: self.npv(disc_curve.DCSpread(yield_curve, r), asof_date) / dirty_price - 1.0,
            -0.99,
            1.00
        )
        return zs


class BondSecurity(base.Security):
    def __init__(self, b: Bond, price: float, asof_date: datetime.date, volume: float = None, avg_price: float = None):
        super().__init__(b, price, asof_date, volume, avg_price)
        self.bond = b
        self.is_price_sane = True

        if self.bond.coupon_pct > 0 and self.bond.coupon_freq is None:
            self.bond.coupon_freq = 2

        if not self.bond.is_taxable:
            self.bond.coupon_pct /= _TAXFREE_CPN_ADJUSTMENT

        if not self.bond.is_price_sane(self.price, asof_date, -0.1, .25):
            if self.bond.is_price_sane(self.price / 100 * self.bond.face_value, asof_date, -0.1, .4):
                self.bond.face_value = 100
            else:
                self.is_price_sane = False

    def dirty_price(self):
        return self.price + self.bond.accrued_interest(self.asof_date)

    def ytm(self):
        if not self.is_price_sane:
            return None
        return self.bond.yield_to_maturity(self.dirty_price(), self.asof_date)

    def zs(self, dc: base.DiscountCurve):
        if not self.is_price_sane:
            return None
        return self.bond.z_spread(dc, self.dirty_price(), self.asof_date)


# bnd = Bond(5.5, datetime.date(2025, 8, 31), datetime.date(2020, 8, 31), 2)
# print([str(d) for d in bnd._coupon_dates()])
# # print([bnd.cashflows().items()])
# ai = bnd.accrued_interest(datetime.date(2022, 9, 1))
# print("Acc Int: ", ai)
# print("NPV: ", bnd.npv(disc_curve.ConstDC(bnd.coupon_pct/100.0)))
# print("YTM: ", bnd.yield_to_maturity(bnd.face_value-0.069))
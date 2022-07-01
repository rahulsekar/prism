import math
import datetime
from scipy import optimize
import numpy as np
#local
import base

_DAYS_IN_YEAR = 365.0


class ConstDC(base.DiscountCurve):
    def __init__(self, r):
        self.r = r

    def yld(self, dt, from_date: datetime.date = datetime.datetime.now()):
        return self.r

    def discount_factor(self, dt: datetime.date, from_date: datetime.date = datetime.datetime.now()):
        return math.pow(1.0 + self.r, (from_date - dt).days / _DAYS_IN_YEAR)


class DCFromBonds(base.DiscountCurve):

    def __init__(self, bnd_secs: list):
        popt, pcov = optimize.curve_fit(
            self.calibrate_func,
            {'bnd_secs': bnd_secs},
            np.array([bnd_sec.price for bnd_sec in bnd_secs]),
            self.init_params_guess()
        )
        self.set_params(*popt)

    def yld(self, dt, from_date: datetime.date = datetime.date.today()):
        yrs = (dt - from_date).days / _DAYS_IN_YEAR
        return math.pow(self.discount_factor(dt, from_date), -1.0 / yrs) - 1.0

    def calibrate_func(self, bnd_secs, *params):
        self.set_params(*params)
        return [bnd_sec.product.npv(self, bnd_sec.asof_date) for bnd_sec in bnd_secs['bnd_secs']]

    def set_params(self, *params):
        raise Exception('Unimplemented')

    def init_params_guess(self):
        raise Exception('Unimplemented')


class NelsonSiegel(DCFromBonds):
    def set_params(self, b0, b1, b2, tau):
        self.b0 = b0
        self.b1 = b1
        self.b2 = b2
        self.tau = tau

    def init_params_guess(self):
        return [0.05, 0.0, 0.0, 2.0]

    def discount_factor(self, dt: datetime.date, from_date: datetime.date = datetime.datetime.now()):
        yrs = (dt - from_date).days / 365.0
        m_tau = yrs / self.tau # m / tau
        exp_m_tau = np.exp(-m_tau)
        rate = self.b0 +\
               (self.b1 + self.b2) * (1.0 - exp_m_tau) / m_tau -\
               self.b2 * exp_m_tau

        if 1.0 + rate < 0.0:
            return 0
        return math.pow(1.0 + rate, -yrs)

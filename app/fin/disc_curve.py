import datetime
import math
from scipy import optimize
import numpy as np

#locals
import asof

class DiscountCurve(object):
    
    def DF(self, date):
        raise Exception('Unimplemented')

class ConstDC(DiscountCurve):

    def __init__(self, r):
        self.r = r

    def DF(self, date):
        return math.pow(1.0 + self.r,
                        (asof.date - date).days / 365.0)

class DCFromBonds(DiscountCurve):

    def __init__(self, bnds):

        popt, pcov = optimize.curve_fit(
            self.calibrate_func,
            bnds,
            [bnd.dirty_price for bnd in bnds],
            self.init_params_guess())
        self.set_params(*popt)

    def calibrate_func(self, bnds, *params):
        self.set_params(*params)
        return [bnd.NPV(self) for bnd in bnds]

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

    def DF(self, date):
        yrs = (date - asof.date).days / 365.0
        m_tau = yrs / self.tau # m / tau
        exp_m_tau = np.exp(-m_tau)
        rate = self.b0 +\
               (self.b1 + self.b2) * (1.0 - exp_m_tau) / m_tau -\
               self.b2 * exp_m_tau

        if 1.0 + rate < 0.0:
            return 0
        return math.pow(1.0 + rate, -yrs)

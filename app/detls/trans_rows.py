import datetime
#locals
import json
from ..db import tables
from .. import consts

class TransformRow(object):
    def init_from_json(self, string):
        raise 'unimplemented'
    def to_json(self):
        raise 'unimplemented'
    def prod_ref(self):
        raise 'unimplemented'
    def level(self):
        raise 'unimplemented'


class TransRowEquity(TransformRow):
    def __init__(self):
        self.sym = self.typ = self.close = self.prod_id = None
        self.opt_typ = consts.OptType.NA
        self.strk = 0
        self.exp = datetime.date.max

    def to_json(self):
        return json.dumps([
            self.typ,
            self.sym,
            self.exp.__str__(),
            self.strk,
            self.opt_typ,
            self.close])

    def init_from_json(self, string):
        [self.typ,
         self.sym,
         self.exp,
         self.strk,
         self.opt_typ,
         self.close] = json.loads(string)

        self.exp = datetime.datetime.strptime(
            self.exp, '%Y-%m-%d').date()

    def prod_ref(self):
        return tables.Equity(
            typ = self.typ,
            symbol = self.sym,
            expiry = self.exp,
            strike = self.strk,
            opt_typ = self.opt_typ)
            
    def level(self):
        return self.close

class TransRowDebt(TransformRow):
    
    def __init__(self):
        self.typ = self.sym = self.maturity = self.issue_date = None
        self.coupon = self.coupon_freq = self.prod_id = None

    def to_json(self):
        return json.dumps([self.typ,
                           self.sym,
                           self.coupon,
                           self.maturity.__str__(),
                           self.issue_date.__str__(),
                           self.coupon_freq,
                           self.wtd_price])

    def init_from_json(self, string):
        [self.typ,
         self.sym,
         self.coupon,
         self.maturity,
         self.issue_date,
         self.coupon_freq,
         self.wtd_price] = json.loads(string)

        self.maturity = datetime.datetime.strptime(
            self.maturity, '%Y-%m-%d').date()

        self.issue_date = datetime.datetime.strptime(
            self.issue_date, '%Y-%m-%d').date()

    def prod_ref(self):
        return tables.Debt(
            typ = self.typ,
            symbol = self.sym,
            coupon = self.coupon,
            maturity = self.maturity,
            issue_date = self.issue_date,
            coupon_freq = self.coupon_freq)

    def level(self):
        return self.wtd_price

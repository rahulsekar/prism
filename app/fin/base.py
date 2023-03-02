import datetime
from abc import abstractmethod


class Product:
    def __init__(self, isin: str):
        self.isin = isin


class DiscountCurve:
    @abstractmethod
    def discount_factor(self, dt: datetime.date, from_date: datetime.date = datetime.datetime.now()):
        pass

    @abstractmethod
    def yld(self, dt, from_date: datetime.date = datetime.datetime.now()):
        pass


class Security:
    def __init__(self, p: Product, price: float, asof_date: datetime.date, volume: float = None, avg_price: float = None,
                 bid_price: float = None, ask_price: float = None):
        self.product = p
        self.price = price
        self.volume = volume
        self.avg_price = avg_price
        self.bid_price = bid_price
        self.ask_price = ask_price
        self.asof_date = asof_date
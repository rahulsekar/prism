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
    def __init__(self, p: Product, price: float, asof_date: datetime.date, volume: float):
        self.product = p
        self.price = price
        self.volume = volume
        self.asof_date = asof_date
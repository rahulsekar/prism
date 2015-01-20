#locals
from . import utils, detl, trans_rows
from ..consts import ProdType

class NSEIndex(detl.DETLBase):

    def symbols(self):
        return [ 'CNX Nifty', 'CNX Bank', 'CNX IT',
                 'CNX Infrastructure' ]

    def url(self):
        return 'http://www.nseindia.com/content/indices/%s' %\
            self.extract_file()

    def extract_file(self):
        return 'ind_close_all_%s.csv' % self.date.strftime('%d%m%Y')
        
    def transform_row_class(self):
        return trans_rows.TransRowEquity

    def get_transform_row(self, row):
        
        tr = self.transform_row_class()()
        
        if row[0] not in self.symbols():
            return tr
        
        tr.sym = row[0]
        tr.typ = ProdType.index
        tr.close = row[5]

        return tr

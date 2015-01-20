import datetime

#locals
import utils, detl, trans_rows
from ..consts import ProdType, OptType

class BSEDeriv(detl.DETLBase):

    def symbols(self):
        return [ 'BSX' ]

    def url(self):
        return 'http://www.bseindia.com/download/Bhavcopy/' +\
            'Derivative/bhavcopy%s.zip' % self.date.strftime('%d-%m-%y')

    def extract_file(self):
        return 'bhavcopy%s.csv' % self.date.__str__()

    def extract(self):
        xl_to_extract = 'bhavcopy%s.xls' %\
                        self.date.strftime('%d-%m-%y')
        utils.extract_zip(self.download_file(), xl_to_extract)
        utils.extract_xl(xl_to_extract, self.extract_file())

    def transform_row_class(self):
        return trans_rows.TransRowEquity

    def get_transform_row(self, row):

        tr = self.transform_row_class()()

        for sym in self.symbols():
            if row[1].startswith(sym):
                tr.sym = sym

        if tr.sym is None:
            return tr

        tr.close = float(row[8])
        tr.exp = datetime.datetime.strptime(row[2], '%Y-%m-%d').date()

        if 'IF' == row[0]:
            tr.typ = ProdType.idx_fut
        elif 'IO' == row[0]:
            tr.typ = ProdType.idx_opt
            tr.strk = float(row[3])
            if 'PUT' == row[4]:
                tr.opt_typ = OptType.PE
            elif 'CALL' == row[4]:
                tr.opt_typ = OptType.CE
            else:
                raise 'Unknown option type', row[4]
        else:
            raise 'Uknown product type', row[0]

        return tr

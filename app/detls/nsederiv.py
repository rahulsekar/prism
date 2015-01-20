import datetime

#locals
import utils
import detl
import trans_rows
from ..consts import ProdType, OptType

class NSEDeriv(detl.DETLBase):

    def symbols(self):
        return [ 'NIFTY', 'BANKNIFTY', 'CNXIT', 'CNXINFRA' ]

    def extract_file(self):
        mon = self.date.strftime('%b').upper()
        yr = self.date.strftime('%Y')
        dd = self.date.strftime('%d')
        return 'fo%s%s%sbhav.csv' % (dd, mon, yr)

    def url(self):
        mon = self.date.strftime('%b').upper()
        yr = self.date.strftime('%Y')
        return 'http://www.nseindia.com/content/historical' + \
            '/DERIVATIVES/%s/%s/%s.zip' % (yr, mon, self.extract_file())

    def extract(self):
        utils.extract_zip(self.download_file(), self.extract_file())

    def transform_row_class(self):
        return trans_rows.TransRowEquity

    def get_transform_row(self, row):
        
        tr = self.transform_row_class()()

        if row[1] not in self.symbols():
            return tr

        tr.sym = row[1]
        tr.exp = datetime.datetime.strptime(row[2], '%d-%b-%Y').date()
        tr.close = float(row[8])

        if 'FUTIDX' == row[0]:
            tr.typ = ProdType.idx_fut
        elif 'OPTIDX' == row[0]:
            tr.typ = ProdType.idx_opt
            tr.strk = float(row[3])
            if 'CE' == row[4]:
                tr.opt_typ = OptType.CE
            elif 'PE' == row[4]:
                tr.opt_typ = OptType.PE
            else:
                raise 'Unknown option type', row[4]
        else:
            raise 'Unknown product type', row[0]

        return tr

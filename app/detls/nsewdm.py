import datetime
import csv

#locals
from . import utils, detl, trans_rows
from ..consts import ProdType, CouponFreq

class NSEWDM(detl.DETLBase):

    def prod_table(self):
        return 'debt'

    def sec_types(self):
        return ['GS', 'TB']

    def extract_file(self):
        return 'trd%s_sett.csv' % self.date.strftime('%d%m')

    def url(self):
        return "http://www.nseindia.com/content/debt/dly%s.zip" %\
            self.date.strftime('%d%m%Y')

    def wdm_file(self):
        return 'wdmlist_%s.csv' % self.date.strftime('%Y-%m-%d')

    def extract(self):
        utils.extract_zip(self.download_file(), self.extract_file())
        #more download
        #think about making self.urls() returning a list
        wdm_url = 'http://www.nseindia.com/content/debt/wdmlist.csv'
        if not utils.staging_file_exists(self.wdm_file()):
            utils.download_if_mytype(wdm_url,
                                     self.wdm_file(),
                                     utils.csv_headers())
        if not utils.staging_file_exists(self.wdm_file()):
            raise 'Could not download wmd file'

    def is_extracted(self):
        return (utils.staging_file_exists(self.download_file()) and
                utils.staging_file_exists(self.wdm_file()))
        
    def transform_row_class(self):
        return trans_rows.TransRowDebt

    def all_securities(self):

        wdm_fd = open(utils.staging_filepath(self.wdm_file()),'rb')
        dialect = csv.Sniffer().sniff(wdm_fd.read(4096))
        wdm_fd.seek(0)
        secs = []
        for sec in csv.reader(wdm_fd, dialect):
            if sec[0] in self.sec_types():
                sec[2] = float(sec[2].strip('=%"'))
                secs.append(sec)

        return secs

    def get_transform_rows(self):

        dly_fd = open(utils.staging_filepath(self.extract_file()),'rb')
        dialect = csv.Sniffer().sniff(dly_fd.read(4096))
        dly_fd.seek(0)
        rows = csv.reader(dly_fd, dialect)
        secs = self.all_securities()

        ret = []
        for row in rows:
            if row[1] not in self.sec_types():
                continue

            row[3] = float(row[3].strip('%'))
            matches = [sec for sec in secs 
                       if (row[1] == sec[0] and 
                           row[2] == sec[1] and
                           row[3] == sec[2])]

            if len(matches) != 1:
                utils.log(self,
                          'Dropping unidentifiable security %s %s %s' %\
                          (row[2], row[3], matches))
                continue

            match = matches[0]
            tr = self.transform_row_class()()

            if 'GS' == row[1]:
                tr.typ = ProdType.g_sec
                tr.coupon = row[3]
            elif 'TB' == row[1]:
                tr.typ = ProdType.t_bill
                tr.coupon = 0
            else:
                raise Exception('Unknown prod type', row)

            tr.sym = row[2]
            tr.wtd_price = float(row[11])

            tr.maturity = datetime.datetime.strptime(
                match[5], '%d-%b-%Y').date()
            tr.issue_date = datetime.datetime.strptime(
                match[4], '%m/%d/%Y').date()

            if 'Yearly' == match[8]:
                tr.coupon_freq = CouponFreq.yearly
            elif 'Half-Yearly' == match[8]:
                tr.coupon_freq = CouponFreq.half_yearly
            elif match[8].strip() == '':
                tr.coupon_freq = CouponFreq.zero

            ret.append(tr)

        return ret

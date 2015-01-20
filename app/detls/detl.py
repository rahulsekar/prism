import csv
#locals
import utils
from app import db
from app.consts import ProdType

#base class for download extract transform
class DETLBase(object):
    
    def __init__(self, date):
        self.date = date

    def url(self):
        raise Exception('unimplemented')

    def extract_file(self):
        raise Exception('unimplemented')

    def extract(self):
        raise Exception('unimplemented')

    def get_transform_rows(self):
        raise Exception('unimplemented')

    def transform_row_class(self):
        raise Exception('unimplemented')


    #download functions
    def download_file(self):
        return self.url().split('/')[-1]

    def download_types(self):
        if self.download_file().endswith('zip'):
            return utils.zip_headers()
        elif self.download_file().endswith('csv'):
            return utils.csv_headers()

    def is_ready_to_download(self):
        return utils.is_url_mytype(self.url(), self.download_types())

    def is_downloaded(self):
        return utils.staging_file_exists(self.download_file())

    def clean_downloaded(self):
        utils.remove_staging_file(self.download_file())

    def download(self):
        utils.download_if_mytype(self.url(),
                                 self.download_file(),
                                 self.download_types())

    #extract functions
    def is_ready_to_extract(self):
        return utils.staging_file_exists(self.download_file())

    def is_extracted(self):
        return utils.staging_file_exists(self.extract_file())

    def clean_extracted(self):
        utils.remove_staging_file(self.extract_file())

    #transform functions
    def transform_file(self):
        return 'tr_%s_%s.json' %\
            (type(self).__name__, self.date.__str__())

    def is_ready_to_transform(self):
        return utils.staging_file_exists(self.extract_file())

    def is_transformed(self):
        return utils.staging_file_exists(self.transform_file())
    
    def clean_transformed(self):
        utils.remove_staging_file(self.transform_file())

    #implementation for nsederiv, bsederiv, nseindex
    def get_transform_rows(self):
        ret = []
        with open(utils.staging_filepath(
                self.extract_file()), 'rb') as fd:
            dialect = csv.Sniffer().sniff(fd.read(4096))
            fd.seek(0)
            rows = csv.reader(fd, dialect)
            for row in rows:
                tr = self.get_transform_row(row)
                if tr.sym is not None:
                    ret.append(tr)
        return ret

    def transform(self):
        trs = self.get_transform_rows()
        tr_writer = open(
            utils.staging_filepath(self.transform_file()),
            'w')

        for tr in trs:
            tr_writer.write(tr.to_json() + '\n')

        tr_writer.close()

    #check and downloading/extracting/transforming!
    def check_do(self,
                 step,
                 ready_func,
                 done_func,
                 clean_func,
                 func):

        if done_func():
            utils.log(self, 'Already %sed' % step)
        elif ready_func():
            utils.log(self, '%sing...' % step, end='')
            try:
                func()
            except:
                utils.log(self, '%s failed!' % step, ctxt=False)
                clean_func()
                raise
            utils.log(self, 'done', ctxt=False)
            assert done_func()
        else:
            utils.log(self, 'Not ready to %s' % step)

    def check_load(self):
        tr_reader = open(
            utils.staging_filepath(self.transform_file()),
            'r')
        trs = []
        for line in tr_reader:
            tr = self.transform_row_class()()
            tr.init_from_json(line[:-1])
            trs.append(tr)

        next_id = db.utils.max_prod_id() / ProdType.max_type + 1

        for tr in trs:

            prod = tr.prod_ref()
            prod = db.session.merge(prod)

            if prod.prod_id is None:
                prod.prod_id = next_id * ProdType.max_type +\
                               prod.typ
                next_id += 1

            level = db.tables.Level(
                prod_id = prod.prod_id,
                date = self.date,
                value = tr.level())
            db.session.merge(level)

        db.session.commit()

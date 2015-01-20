import os
import requests
import zipfile
import xlrd
import datetime
import sys

#locals
from app.config import DATA_STAGING_DIR

def staging_filepath(filename):
    return DATA_STAGING_DIR + '/' + filename

def log(obj, msg, end='\n', ctxt=True):
    
    if ctxt:
        context = '%s %s: ' % (obj.date.__str__(),
                               type(obj).__name__)
    else:
        context = ''

    sys.stdout.write('%s%s%s' % (context, msg, end))
    sys.stdout.flush()

def staging_file_exists(filename):
    return os.path.isfile(staging_filepath(filename))

def remove_staging_file(filename):
    if staging_file_exists(filename):
        os.remove(staging_filepath(filename))

def zip_headers():
    return ['application/x-zip-compressed', 'application/zip']

def csv_headers():
    return ['application/csv']

def is_url_mytype(url, types):
    return (requests.head(url).headers['content-type'] in types)

def save_request_result(r, filename):
    filepath = staging_filepath(filename)
    with open(filepath, 'wb') as fd:
        for chunk in r.iter_content(4096):
            fd.write(chunk)

def download_if_mytype(url, filename, types):
    r = requests.get(url, stream=True)
    if r.headers['content-type'] in types:
        save_request_result(r, filename)
        return True
    else:
        return False

def extract_zip(zip_file, file_to_extract):
    zd = zipfile.ZipFile(staging_filepath(zip_file), 'r')
    zd.extract(file_to_extract, DATA_STAGING_DIR)

def extract_xl(xl_file, csv_file):
        wb = xlrd.open_workbook(staging_filepath(xl_file))
        ws = wb.sheet_by_name('Sheet1')
        writer = open(staging_filepath(csv_file), 'w')
       
        for r in range(1, ws.nrows):
            ln = []
            for c in range(ws.ncols):
                typ = ws.cell_type(r,c)
                val = ws.cell_value(r,c)
                if xlrd.XL_CELL_DATE == typ:
                    (y,m,d,h,mi,s) = xlrd.xldate_as_tuple(
                        val, wb.datemode)
                    val = datetime.date(y,m,d)
                ln.append(val.__str__())

            writer.write(','.join(ln) + '\n')
        writer.close()

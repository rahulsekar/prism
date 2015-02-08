import datetime, os, json

#locals
from app import db
from app.consts import ProdType
from app.config import JSON_DIR

def levels(days=30):
    start_date = datetime.date.today() - datetime.timedelta(days=days)
    avail = dict((x,y)
                for x,y in db.utils.level_count_by_date(start_date))
    
    dts = [datetime.date.today() - datetime.timedelta(days=d)
           for d in range(days+1)]
    rows = []
    for dt in dts:
        if dt.weekday() < 5:
            val = 0
            if dt in avail:
                val = avail[dt]
            rows.append([dt.__str__(), val])

    return {
        'header': ['Date', 'Prices'],
        'rows' : rows
    }
    
def prods():
    res = db.utils.prod_count_by_typ(db.tables.Equity)
    res += db.utils.prod_count_by_typ(db.tables.Debt)
    header = ['Type', 'Count']
    mems = vars(ProdType)
    rows = []
    for row in res:
        for mem in mems:
            if not mem.startswith('__') and mems[mem] == row[0]:
                rows.append([mem, row[1]])
    return {
        'header' : header,
        'rows' : rows,
    }

def generate():
    as_of = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return json.dumps({
        'prods' : prods(),
        'levels' : levels(),
        'asof' : as_of
    })


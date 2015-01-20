import sys, datetime

#locals
from app.fin import yield_curve
from app.detls import loader
from app.server import app
from app.config import WWW_DEBUG

command = sys.argv[1]

if 'loader' == command:
    date = datetime.datetime.strptime(sys.argv[2],
                                      '%Y-%m-%d').date()
    loader.load(date)
elif 'plots' ==  command:
    for dtstr in sys.argv[2].split(','):
        date = datetime.datetime.strptime(dtstr,
                                          '%Y-%m-%d').date()
        yield_curve.generate_yield_curve(date)
elif 'server' == command:
    app.run(debug=WWW_DEBUG)
else:
    raise Exception('Unknown command')

from flask import Flask, render_template
import datetime, json

#locals
from app.fin import yield_curve
from app.detls import status, loader

app = Flask(__name__)

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/prepare/yield_curve/<asofstr>')
def yc(asofstr):
    asofdate = datetime.datetime.strptime(asofstr, '%Y-%m-%d').date()
    yield_curve.check_generate(asofdate)
    return 'OK'

@app.route('/prepare/data_status')
def data_status():
    status.check_generate()
    return 'OK'

@app.route('/prepare/data_load/<asofstr>')
def data_load(asofstr):
    date = datetime.datetime.strptime(asofstr, '%Y-%m-%d').date()
    loader.load(date)
    status.generate()
    return 'OK'

if '__main__' == __name__:
    app.run()

from flask import Flask, render_template
import datetime, json

#locals
from app.fin import asof, bondfns

app = Flask(__name__)

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/bonds/<asofstr>')
def bonds(asofstr):
    asof.date = datetime.datetime.strptime(asofstr,
                                          '%Y-%m-%d').date()
    bnds = bondfns.get_traded_treasury_bonds()
    return json.dumps([bnd.to_dict() for bnd in bnds])

if '__main__' == __name__:
    app.run()

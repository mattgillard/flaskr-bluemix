# all the imports
import os
import MySQLdb
from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash
from contextlib import closing
from MySQLdb.cursors import DictCursor

# configuration
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'root'
PASSWORD = 'default'

# create our little application :)
app = Flask(__name__)
app.config.from_object(__name__)

def connect_db():
## Pull in CloudFoundry's production settings
  if 'VCAP_SERVICES' in os.environ:
    import json
    vcap_services = json.loads(os.environ['VCAP_SERVICES'])
    # XXX: avoid hardcoding here
    mysql_srv = vcap_services['cleardb'][0]
    cred = mysql_srv['credentials']
    return MySQLdb.connect(host=cred['hostname'], # your host, usually localhost
                     user=cred['username'], # your username
                      passwd=cred['password'], # your password
                      db=cred['name']) # name of the data base
  else:
    return MySQLdb.connect(host="localhost", # your host, usually localhost
                     user=app.config['USERNAME'], # your username
                      passwd="", # your password
                      db="test") # name of the data base
def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql', mode='r') as f:
	    contents=f.read()
	    print contents
            db.cursor().execute(contents)
        db.commit()

@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

@app.route('/')
def show_entries():
    cur = g.db.cursor(DictCursor)
    query = 'select title, text from entries order by id desc'
    cur.execute(query)
    entries = [dict(title=row['title'].decode('utf-8'), text=row['text'].decode('utf-8')) for row in cur.fetchall()]
    return render_template('show_entries.html', entries=entries)

@app.route('/add', methods=['POST'])
def add_entry():
    if not session.get('logged_in'):
        abort(401)
    cur = g.db.cursor()
    cur.execute('insert into entries (title, text) values(%s,%s)',
                [request.form['title'].encode('utf-8'), request.form['text'].encode('utf-8')])
    cur.close()
    g.db.commit()
    flash('New entry was successfully posted')
    return redirect(url_for('show_entries'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('show_entries'))
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_entries'))

port = os.getenv('VCAP_APP_PORT', '5000')
if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=int(port))


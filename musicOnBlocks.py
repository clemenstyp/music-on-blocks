#!/usr/bin/env python
from __future__ import print_function


import os
import sqlite3
import errno
from backend.MusicLogging import MusicLogging


# noinspection PyCompatibility
import thread


from flask import Flask, request, session, g, redirect, url_for, abort, \
    render_template, flash, Response
from flask_nav import Nav
from flask_nav.elements import Navbar, View, Subgroup, Link, Text, Separator
from flask_bootstrap import Bootstrap

from backend.sonosController import SonosController

import subprocess
import os

os.system("sh pigpiod.sh")

def get_git_revision_hash():
    return subprocess.check_output(['git', 'rev-parse', 'HEAD'])

def get_git_revision_short_hash():
    return subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'])

app = Flask(__name__)
app.config.from_pyfile('settings.py')
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, app.config['DATABASE_NAME']),
))

# We're adding a navbar as well through flask-navbar. In our example, the
# navbar has an usual amount of Link-Elements, more commonly you will have a
# lot more View instances.
nav = Nav()
nav.register_element('frontend_top', Navbar(
    View('Music on Blocks', 'index'),
    View('Debug-Info', 'index'),
    View('Time Log', 'index'),
    View('Log', 'DebugApi:showLog'),
    # Subgroup(
    #     'Docs',
    #     Link('Flask-Bootstrap', 'http://pythonhosted.org/Flask-Bootstrap'),
    #     Link('Flask-AppConfig', 'https://github.com/mbr/flask-appconfig'),
    #     Link('Flask-Debug', 'https://github.com/mbr/flask-debug'),
    #     Separator(),
    #     Text('Bootstrap'),
    #     Link('Getting started', 'http://getbootstrap.com/getting-started/'),
    #     Link('CSS', 'http://getbootstrap.com/css/'),
    #     Link('Components', 'http://getbootstrap.com/components/'),
    #     Link('Javascript', 'http://getbootstrap.com/javascript/'),
    #     Link('Customize', 'http://getbootstrap.com/customize/'), ),
    Text('Current GIT Hash: {}'.format(get_git_revision_short_hash())), ))

# webapp endpoint
Bootstrap(app)
nav.init_app(app)

# Because we're security-conscious developers, we also hard-code disabling
# the CDN support (this might become a default in later versions):
app.config['BOOTSTRAP_SERVE_LOCAL'] = True


raspberryPi = None
mySonosController = None
lastTag = None

# database stuff
def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv

def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


# noinspection PyUnusedLocal
@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


def init_db():
    """Initializes the database."""
    with app.app_context():
        db = get_db()
        with app.open_resource('backend/schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


@app.cli.command('initdb')
def initdb_command():
    """Initializes the database."""
    init_db()
    MusicLogging.Instance().info('Initialized the database.')


def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


if not os.path.exists(app.config['DATABASE']):
    init_db()
    MusicLogging.Instance().info('Initialized the database.')


# commen commands

def startOneLedPulse():
    if raspberryPi:
        raspberryPi.startOnePulseLed()
    else:
        MusicLogging.Instance().info("one LED pulse")


def touchCallback(aTag):
    with app.app_context():
        # within this block, current_app points to app.
        #aTag = str(aHexTag).encode("hex")  # get the UID of the touched tag
        global lastTag
        lastTag = aTag
        touchedTag(aTag)
        return True


def releaseCallback():
    with app.app_context():
        # within this block, current_app points to app.
        global lastTag
        lastTag = None
        mySonosController.saveLastTagTime()
        mySonosController.pause()
        return True


def startSonos():
    global raspberryPi
    global mySonosController

    # posibillity to start a demo controller
    mySonosController = SonosController(dayVol=app.config['DAY_VOL'], nightVol=app.config['NIGHT_VOL'],
                                        daytimeRange=app.config['DAYTIME_RANGE'], unjoin=app.config['UNJOIN'],
                                        clear=True,
                                        restartTime=app.config['RESTART_TIME'])
    mySonosController.startSonos(app.config['SONOS_IP'])

    if not app.config['RPI_DEMO']:
        from backend.rpi import RaspberryPi
        raspberryPi = RaspberryPi(app.config['NFC_READER'], pause, play, togglePlayPause, toggleNext, togglePrev,
                                  toggleUnjoin, toggleVolUp, toggleVolDown, toggleShuffle, rightRotaryTurn,
                                  leftRotaryTurn, rotaryTouch)

    while True:
        if raspberryPi:
            raspberryPi.readNFC(touchCallback, releaseCallback)


# noinspection PyUnusedLocal
def togglePlayPause(event):
    startOneLedPulse()
    mySonosController.playPause()


# noinspection PyUnusedLocal
def pause(event):
    startOneLedPulse()
    mySonosController.pause()


# noinspection PyUnusedLocal
def play(event):
    startOneLedPulse()
    mySonosController.play()


# noinspection PyUnusedLocal
def toggleNext(event):
    startOneLedPulse()
    mySonosController.next()


# noinspection PyUnusedLocal
def togglePrev(event):
    startOneLedPulse()
    mySonosController.previous()


# noinspection PyUnusedLocal
def toggleUnjoin(event):
    startOneLedPulse()
    mySonosController.unjoinForced()


# noinspection PyUnusedLocal
def toggleVolUp(event):
    startOneLedPulse()
    mySonosController.volumeUp(1)


# noinspection PyUnusedLocal
def toggleVolDown(event):
    startOneLedPulse()
    mySonosController.volumeUp(-1)


# noinspection PyUnusedLocal
def toggleShuffle(event):
    startOneLedPulse()
    mySonosController.togglePlayModeShuffle()
    # it schoud toggle between shufffle and normal


# noinspection PyUnusedLocal
def leftRotaryTurn(event):
    mySonosController.volumeUp(-3)


# noinspection PyUnusedLocal
def rightRotaryTurn(event):
    mySonosController.volumeUp(3)


# noinspection PyArgumentList,PyUnusedLocal
def rotaryTouch(event):
    togglePlayPause()


def touchedTag(aTag):
    entry = query_db('select * from entries where tag_id = ?', [aTag], one=True)
    if entry:
        startOneLedPulse()
        mySonosController.play(entry)
    else:
        MusicLogging.Instance().info('no entry found')


# flask web views

@app.route('/')
def show_entries():
    entries = query_db('select * from entries order by id desc')
    return render_template('show_entries.html', entries=entries)


@app.route('/update/<entrieID>')
def update_cache(entrieID):
    entry = query_db('select * from entries where id = ?', [entrieID], one=True)
    if entry is None:
        flash('nothing found, try again')
    else:
        playitems = mySonosController.getCache(entry)
        db = get_db()
        db.execute("UPDATE entries SET playitems = ? WHERE id = ?", [playitems, entrieID])
        db.commit()
        # noinspection PyTypeChecker
        flash('Updated cache for "' + entry['title'] + '"')

    return redirect(url_for('show_entries'))


@app.route('/add', methods=['POST'])
def add_entry():
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    title = request.form['title']
    comment = request.form['comment']
    tag_id = request.form['tag_id']
    time_offset = request.form['time_offset']
    volume = request.form['volume']
    item = request.form['item']
    itemType = request.form['type']
    db.execute(
        'INSERT INTO entries (title, comment, tag_id, time_offset, volume, item, type) VALUES (?, ?, ?, ?, ?, ?, ?)',
        [title, comment, tag_id, time_offset, volume, item, itemType])
    db.commit()
    flash('New entry was successfully posted')
    return redirect(url_for('show_entries'))


@app.route('/remove/<entrieID>')
def remove_entry(entrieID):
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    db.execute('DELETE FROM entries WHERE id=?', [entrieID])
    db.commit()
    flash('New entry was successfully removed')
    return redirect(url_for('show_entries'))


@app.route('/play/<entrieID>')
def play_entry(entrieID):
    entry = query_db('select * from entries where id = ?',
                     [entrieID], one=True)
    if entry is None:
        flash('nothing found, try again')
    else:
        startOneLedPulse()
        # Look up the song to play and set the right volume depending on whether it's day or night
        mySonosController.play(entry)
        # noinspection PyTypeChecker
        flash('Playing entry "' + entry['title'] + '"')

    return redirect(url_for('show_entries'))


@app.route('/write/<entrieID>')
def write_entry(entrieID):
    if not session.get('logged_in'):
        abort(401)
    entry = query_db('select * from entries where id = ?', [entrieID], one=True)
    if entry is None:
        flash('nothing found, try again')
    else:
        global lastTag
        if lastTag:
            db = get_db()
            db.execute("UPDATE entries SET tag_id = ? WHERE id = ?", [lastTag, entrieID])
            db.commit()
            # noinspection PyTypeChecker
            flash('Updated tag id for "' + entry['title'] + '" to "' + lastTag + '"')
        else:
            flash('no tag found')

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


def get_file(filename):  # pragma: no cover
    try:
        src = os.path.join(app.root_path, filename)
        # Figure out how flask returns static files
        # Tried:
        # - render_template
        # - send_file
        # This should not be so non-obvious
        return open(src).read()
    except IOError as exc:
        return str(exc)

@app.route('/log')
def log():
    src = os.path.join(app.root_path, LOG_FILENAME)
    try:
        log = get_file(src)
        return Response(log, mimetype="text/plain")
    except Exception as e:
        return str(e)


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_entries'))


try:
    thread.start_new_thread(startSonos, ())
except:
    MusicLogging.Instance().info("Error: unable to start thread")

import signal
import sys
def signal_handler(signal, frame):
    MusicLogging.Instance().info('You pressed Ctrl+C!')
    mySonosController.stopAll()
    raspberryPi.stopAll()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)

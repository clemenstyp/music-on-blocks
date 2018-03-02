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
    View('Tags', 'tags'),
    View('Settings', 'settings'),
    View('Debug', 'debug'),
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

    set_default_settings()

def set_default_settings():
    with app.app_context():
        db = get_db()
        item = 'SPEAKER'
        value = 'Schlafzimmer'
        comment = 'Wie heisst der Raum in dem die Musik abgespielt werden soll'
        db.execute('INSERT INTO settings (item, value, comment) VALUES (?, ?, ?)', [item, value, comment])
        db.commit()

        item = 'NFC_READER'
        value = 'demo'
        comment = 'MFRC522 ist der Reader von Clemens, pn532 ist der Reader von Johannes, demo ist demo'
        db.execute('INSERT INTO settings (item, value, comment) VALUES (?, ?, ?)', [item, value, comment])
        db.commit()

        # NFC_READER = "MFRC522"  # MFRC522 ist der Reader von Clemens
        # NFC_READER = "pn532"  #   pn532 ist der Reader von Johannes
        # NFC_READER = "demo"  # pn532 ist der Reader von Johannes

        item = 'DAY_VOL'
        value = '100'
        comment = 'max daytime volume, 100 means no volume change'
        db.execute('INSERT INTO settings (item, value, comment) VALUES (?, ?, ?)', [item, value, comment])
        db.commit()

        item = 'NIGHT_VOL'
        value = '20'
        comment = 'max nighttime volume'
        db.execute('INSERT INTO settings (item, value, comment) VALUES (?, ?, ?)', [item, value, comment])
        db.commit()

        item = 'DAYTIME_RANGE'
        value = '7-17'
        comment = 'daytime is 7:00a to 5:59p'
        db.execute('INSERT INTO settings (item, value, comment) VALUES (?, ?, ?)', [item, value, comment])
        db.commit()

        item = 'UNJOIN'
        value = 'False'
        comment = 'True oder False'
        db.execute('INSERT INTO settings (item, value, comment) VALUES (?, ?, ?)', [item, value, comment])
        db.commit()

        item = 'RPI_DEMO'
        value = 'True'
        comment = 'bei True verbindet ist er nicht auf einem rPi (test auf PC)'
        db.execute('INSERT INTO settings (item, value, comment) VALUES (?, ?, ?)', [item, value, comment])
        db.commit()

        item = 'RESTART_TIME'
        value = '30'
        comment = 'Restart Time in Seconds'
        db.execute('INSERT INTO settings (item, value, comment) VALUES (?, ?, ?)', [item, value, comment])
        db.commit()




@app.cli.command('initdb')
def initdb_command():
    """Initializes the database."""
    init_db()
    MusicLogging.Instance().info('Initialized the database.')

#once init the db
#init_db()

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
        MusicLogging.Instance().info("touchCallback")
        global lastTag
        lastTag = aTag
        touchedTag(aTag)
        return True


def releaseCallback():
    with app.app_context():
        # within this block, current_app points to app.
        MusicLogging.Instance().info("releaseCallback")
        global lastTag
        lastTag = None
        mySonosController.saveLastTagTime()
        mySonosController.pause()
        return True


killSonos = True

def startSonos():
    global raspberryPi
    global mySonosController
    global killSonos
    killSonos = False
    # posibillity to start a demo controller
    mySonosController = SonosController(dayVol=get_settings('DAY_VOL'), nightVol=get_settings('NIGHT_VOL'),
                                        daytimeRange=get_settings('DAYTIME_RANGE'), unjoin=get_settings('UNJOIN'),
                                        clear=True,
                                        restartTime=get_settings('RESTART_TIME'))
    mySonosController.startSonos(get_settings('SPEAKER'))

    rpi_demo = get_settings('RPI_DEMO')
    if rpi_demo != "True":
        from backend.rpi import RaspberryPi
        raspberryPi = RaspberryPi(get_settings('NFC_READER'), pause, play, togglePlayPause, toggleNext, togglePrev,
                                  toggleUnjoin, toggleVolUp, toggleVolDown, toggleShuffle, rightRotaryTurn,
                                  leftRotaryTurn, rotaryTouch)

    while True and not killSonos:
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


def get_settings(settings_item):
    with app.app_context():
        entry = query_db('select * from settings where item = ?', [settings_item], one=True)
        if entry is None:
           return ""
        else:
            return entry['value']

# flask web views
@app.route('/next')
def next():
    startOneLedPulse()
    mySonosController.next()
    return redirect(url_for('index'))

@app.route('/prev')
def prev():
    startOneLedPulse()
    mySonosController.previous()
    return redirect(url_for('index'))

@app.route('/lauter')
def lauter():
    startOneLedPulse()
    mySonosController.volumeUp(3)
    return redirect(url_for('index'))

@app.route('/leiser')
def leiser():
    startOneLedPulse()
    mySonosController.volumeUp(-3)
    return redirect(url_for('index'))


@app.route('/')
def index():
    return render_template('content-start.html', headline="Music-On-Blocks")

@app.route('/tags')
def tags():
    entries = query_db('select * from entries order by id desc')
    return render_template('content-entries.html', contentArray=entries)


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

    return redirect(url_for('tags'))


@app.route('/updateAll')
def update_all():
    entries = query_db('select * from entries order by id desc')
    result = ""
    for entry in entries:
        playitems = mySonosController.getCache(entry)
        db = get_db()
        db.execute("UPDATE entries SET playitems = ? WHERE id = ?", [playitems, entry['id']])
        db.commit()
        # noinspection PyTypeChecker
        if result is "":
            result = entry['title']
        else:
            result = result + " - " + entry['title']

    flash('Updated cache for: "' + result + '"')
    return redirect(url_for('tags'))



@app.route('/add', methods=['POST'])
def add_entry():
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    cur = db.cursor()

    title = request.form['title']
    comment = request.form['comment']
    tag_id = request.form['tag_id']
    time_offset = request.form['time_offset']
    volume = request.form['volume']
    item = request.form['item']
    itemType = request.form['type']
    cur.execute(
        'INSERT INTO entries (title, comment, tag_id, time_offset, volume, item, type) VALUES (?, ?, ?, ?, ?, ?, ?)',
        [title, comment, tag_id, time_offset, volume, item, itemType])
    db.commit()
    entrieID = cur.lastrowid
    cur.close()

    flash('New entry was successfully posted')
    return redirect(url_for('update_cache', entrieID=entrieID))


@app.route('/save/<entrieID>', methods=['POST'])
def save_entry(entrieID):
    if not session.get('logged_in'):
        abort(401)
    entry = query_db('select * from entries where id = ?', [entrieID], one=True)
    if entry is None:
        flash('nothing found, try again')
    else:
        title = request.form['title']
        comment = request.form['comment']
        tag_id = request.form['tag_id']
        time_offset = request.form['time_offset']
        volume = request.form['volume']
        item = request.form['item']
        itemType = request.form['type']

        db = get_db()
        if title is not entry['title']:
            db.execute("UPDATE entries SET title = ? WHERE id = ?", [title, entrieID])
            db.commit()
        if comment is not entry['comment']:
            db.execute("UPDATE entries SET comment = ? WHERE id = ?", [comment, entrieID])
            db.commit()
        if tag_id is not entry['tag_id']:
            db.execute("UPDATE entries SET tag_id = ? WHERE id = ?", [tag_id, entrieID])
            db.commit()
        if time_offset is not entry['time_offset']:
            db.execute("UPDATE entries SET time_offset = ? WHERE id = ?", [time_offset, entrieID])
            db.commit()
        if volume is not entry['volume']:
            db.execute("UPDATE entries SET volume = ? WHERE id = ?", [volume, entrieID])
            db.commit()
        if item is not entry['item']:
            db.execute("UPDATE entries SET item = ? WHERE id = ?", [item, entrieID])
            db.commit()
        if itemType is not entry['type']:
            db.execute("UPDATE entries SET type = ? WHERE id = ?", [itemType, entrieID])
            db.commit()
        # noinspection PyTypeChecker
        flash('Updated entrie with id "' + entrieID + '"')

    return redirect(url_for('update_cache', entrieID=entrieID))


@app.route('/remove/<entrieID>')
def remove_entry(entrieID):
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    db.execute('DELETE FROM entries WHERE id=?', [entrieID])
    db.commit()
    flash('New entry was successfully removed')
    return redirect(url_for('tags'))


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

    return redirect(url_for('tags'))


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

    return redirect(url_for('tags'))


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
            return redirect(url_for('tags'))
    #return render_template('login.html', error=error)
    return render_template('content-login.html', error=error)


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

@app.route('/settings')
def settings():
    entries = query_db('select * from settings order by id desc')
    return render_template('content-settings.html', settingsArray=entries)


@app.route('/save_settings', methods=['POST'])
def save_settings():
    if not session.get('logged_in'):
        abort(401)

    db = get_db()
    form = request.form
    for key in form.keys():
        for value in form.getlist(key):
            db.execute("UPDATE settings SET value = ? WHERE id = ?", [value, key])
            db.commit()

    global killSonos
    killSonos = True
    import time
    time.sleep(3)

    try:
        sonosThread = thread.start_new_thread(startSonos, ())
    except:
        MusicLogging.Instance().info("Error: unable to start thread")
    # noinspection PyTypeChecker
    flash('Updated settings')

    return redirect(url_for('settings'))


def readFile(filename):
    if not os.path.isfile(filename):
        return ''
    aFile = open(filename, "r")
    returnValue = aFile.read()
    aFile.close()
    return returnValue

def getLog(filename, numberOfLines = -1):
    fullLog = str(readFile(filename)).decode('ascii', 'ignore')
    allLines = fullLog.splitlines()
    if numberOfLines == -1:
        selectedLines = allLines[::-1]
    else:
        selectedLines = allLines[:((numberOfLines +1) * -1):-1]

    log = '\r\n'.join(selectedLines)
    return log


@app.route('/debug')
def debug():
    log_filename = os.path.join(app.root_path, MusicLogging.Instance().filename())
    content = str(getLog(log_filename, 1000))
    return render_template('content.html', contentDebug=content, headline="Debug Log")



@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('index'))


try:
    sonosThread = thread.start_new_thread(startSonos, ())
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

#!/usr/bin/env python
from __future__ import print_function
from time import sleep

from sonosController import SonosController
import sonosController
import logging
from logging.handlers import RotatingFileHandler

import time
import hashlib
import json

import requests
import os
import sqlite3
from time import strftime
import traceback
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash, jsonify
import thread
import time


app = Flask(__name__)

app.config.from_pyfile('settings.py')
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, app.config['DATABASE_NAME']),
))

raspberryPi = None
sonosController = None
lastTag = None
#database stuff

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


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

def init_db():
    """Initializes the database."""
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

@app.cli.command('initdb')
def initdb_command():
    """Initializes the database."""
    init_db()
    print
    'Initialized the database.'

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

if not os.path.exists(app.config['DATABASE']):
    init_db()
    print('Initialized the database.')

# commen commands

def startOneLedPulse():
    if raspberryPi:
        raspberryPi.startOnePulseLed()
    else:
        print("one LED pulse")


def touchCallback(aHexTag):
    with app.app_context():
    # within this block, current_app points to app.
        aTag = str(aHexTag).encode("hex")  # get the UID of the touched tag
        global lastTag
        lastTag = aTag
        touchedTag(aTag)
        return True
    return False

def releaseCallback():
    with app.app_context():
    # within this block, current_app points to app.
        global lastTag
        lastTag = None
        sonosController.saveLastTagTime()
        sonosController.pause()
        return True
    return False

def startSonos():
    global raspberryPi
    global sonosController

    #posibillity to start a demo controller
    sonosController = SonosController(dayVol=app.config['DAY_VOL'], nightVol=app.config['NIGHT_VOL'], daytimeRange=app.config['DAYTIME_RANGE'], unjoin=app.config['UNJOIN'], clear=True, restartTime=app.config['RESTART_TIME'])
    sonosController.startSonos(app.config['SONOS_IP'])

    if not app.config['RPI_DEMO']:
        from rpi import RaspberryPi
        raspberryPi = RaspberryPi(app.config['NFC_READER'], pause, play, togglePlayPause, toggleNext, togglePrev, toggleUnjoin, toggleVolUp, toggleVolDown, toggleShuffle, rightRotaryTurn, leftRotaryTurn, rotaryTouch)

    while True:
        if raspberryPi:
            raspberryPi.readNFC(touchCallback, releaseCallback)

# flask web setings

@app.route("/togglePlayPause")
def togglePlayPause():
    startOneLedPulse()
    sonosController.playPause()
    return redirect(url_for('show_entries'))


@app.route("/pause")
def pause():
    startOneLedPulse()
    sonosController.pause()
    return redirect(url_for('show_entries'))


@app.route("/play")
def play():
    startOneLedPulse()
    sonosController.play()
    return redirect(url_for('show_entries'))


@app.route("/toggleNext")
def toggleNext():
    startOneLedPulse()
    sonosController.next()
    return redirect(url_for('show_entries'))


@app.route("/togglePrev")
def togglePrev():
    startOneLedPulse()
    sonosController.previous()
    return redirect(url_for('show_entries'))


@app.route("/toggleUnjoin")
def toggleUnjoin():
    startOneLedPulse()
    sonosController.unjoinForced()
    return redirect(url_for('show_entries'))


@app.route("/toggleVolUp")
def toggleVolUp():
    startOneLedPulse()
    sonosController.volumeUp(1)
    return redirect(url_for('show_entries'))


@app.route("/toggleVolDown")
def toggleVolDown():
    startOneLedPulse()
    sonosController.volumeUp(-1)
    return redirect(url_for('show_entries'))


@app.route("/toggleShuffle")
def toggleShuffle():
    startOneLedPulse()
    sonosController.togglePlayModeShuffle()
    #it schoud toggle between shufffle and normal
    return redirect(url_for('show_entries'))


@app.route("/leftRotaryTurn")
def leftRotaryTurn():
    sonosController.volumeUp(1)
    return redirect(url_for('show_entries'))


@app.route("/rightRotaryTurn")
def rightRotaryTurn():
    sonosController.volumeUp(-1)
    return redirect(url_for('show_entries'))

@app.route("/rotaryTouch")
def rotaryTouch():
    togglePlayPause()
    return redirect(url_for('show_entries'))


@app.route('/touchedTag/<aTag>')
def touchedTag(aTag):
    entry = query_db('select * from entries where tag_id = ?', [aTag], one=True)
    startOneLedPulse()
    sonosController.play(entry)
    return redirect(url_for('show_entries'))

@app.route('/')
def show_entries():
    entries = query_db('select * from entries order by id desc')
    return render_template('show_entries.html', entries=entries)


@app.route('/update/<entrieID>')
def update_cache(entrieID):
    flash('caching currently not possible')
    # entry = query_db('select * from entries where id = ?',
    #                 [entrieID], one=True)
    # if entry is None:
    #     flash('nothing found, try again')
    # else:
    #     playitems = sonosController.getCache(entry)
    #
    #     db.execute("UPDATE entries SET playitems = ? WHERE id = ?", [playitems, entrieID])
    #     db.commit()
    #     flash('Updated cache for "' + entry['title'] + '"')

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
    type = request.form['type']
    db.execute('insert into entries (title, comment, tag_id, time_offset, volume, item, type) values (?, ?, ?, ?, ?, ?, ?)', [title, comment,tag_id, time_offset, volume, item, type ])
    db.commit()
    flash('New entry was successfully posted')
    return redirect(url_for('show_entries'))


@app.route('/remove/<entrieID>')
def remove_entry(entrieID):
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    db.execute('delete from entries where id=?', [entrieID])
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
        sonosController.play(entry)
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


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_entries'))

try:
   thread.start_new_thread( startSonos, () )
except:
   print("Error: unable to start thread")

if __name__ == '__main__':
    app.run(port=8080, debug=True)


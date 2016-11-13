#!/usr/bin/env python
from __future__ import print_function
import time
from datetime import datetime, timedelta
import json
import os.path

from soco import SoCo
from soco.data_structures import DidlObject
from soco.data_structures import DidlResource

class SonosController(object):
    def __init__(self, dayVol=25, nightVol=15, daytimeRange=[7, 17], unjoin=True, clear=True,
                 settingsFolder="settings", restartTime = 10):
        self.dayVol = dayVol
        self.nightVol = nightVol
        self.daytimeRange = daytimeRange
        self.unjoinBool = unjoin
        self.clear = clear
        self.settings = settingsFolder
        self.restartTime = restartTime


    def startSonos(self, sonos_ip):
        if sonos_ip == "demo":
            self.sonos = None
            print("Using Sonos Demo...")
            return

        # Sonos setup
        print("Connecting to Sonos...")
        self.sonos = SoCo(sonos_ip)
        print("Connected to Sonos: " + self.sonos.player_name)

        # Use this section to get the URIs of new songs we want to add
        info = self.get_current_track_info()
        print("Currently Playing: " + info['title'])
        print("URI: " + info['uri'])
        print("---")
        return True

    # def sonosData(self):
    #     # save song.tmp
    #     if os.path.isfile(self.settings + "/" + "1_songs" + ".txt"):
    #         songsJSON = open(self.settings + "/" + "1_songs" + ".txt")
    #         songs = json.load(songsJSON)
    #         songsJSON.close()
    #         fobj_out = open(self.settings + "/"  + "1_songs_TMP-COPY" + ".txt", "w")
    #         fobj_out.write(json.dumps(songs, sort_keys=True, indent=4, separators=(',', ': ')))
    #         fobj_out.close()
    #     else:
    #         songs = {}
    #     return songs

    def getPlayList(self, entry):
        returnItems = []
        if entry['type'] == 'url':
            returnItems = self.getUrlCache(entry)
        elif entry['type'] == 'playlist':
            returnItems = self.getPlaylistCache(entry)
        elif entry['type'] == 'album':
            returnItems = self.getAlbumCache(entry)
        elif entry['type'] == 'artist':
            returnItems = self.getArtistCache(entry)
        elif entry['type'] == 'genre':
            returnItems = self.getGenreCache(entry)

        return returnItems

    def getPlaylistCache(self, entry):
        return self.getMusicLibraryInformationCache('sonos_playlists', entry, 'playlist')

    def getAlbumCache(self, entry):
        return self.getMusicLibraryInformationCache('albums', entry, 'album')

    def getArtistCache(self, entry):
        return self.getMusicLibraryInformationCache('album_artists', entry, 'artist')

    def getGenreCache(self, entry):
        return self.getMusicLibraryInformationCache('genres', entry, 'genre')

    def getUrlCache(self, entry):
        item = DidlResource(uri=entry['item'], protocol_info=None)
        return [item]

    def getMusicLibraryInformationCache(self, searchType, entry, valueType):
        returnItems = []

        startItem = 0
        startAtIndex = 0
        while True:
            returnedItems = 0
            try:
                # self.music_library.get_music_library_information('albums', start, max_items, full_album_art_uri)
                playlist_info = self.sonos.music_library.get_music_library_information(searchType, start=startAtIndex, max_items=100)
                returnedItems = playlist_info.number_returned
            except:
                print("some error")
            if returnedItems == 0:
                break
            if entry['type'] == valueType:
                for playlist in playlist_info:
                    playlistTitle = playlist.title
                    if playlistTitle == entry['item']:
                        print('found ' + entry['item'])
                        try:
                            track_list = self.sonos.music_library.browse(playlist)
                            returnItems.extend(track_list)
                        except:
                            print("some error")
            startAtIndex += returnedItems

        # playlist_info = #sonos.music_library.get_music_library_information('sonos_playlists',search_term='Shovels And Rope')
        #print('Fonud {} Sonos playlists'.format(playlist_info.number_returned))

        return returnItems


    def playItems(self, items):
        startPlaying = False

        for item in items:
            try:
                self.sonos.add_to_queue(item)
            except:
                print("  error adding...")
            if startPlaying == False:
                try:
                    startPlaying = self.sonos.play_from_queue(0, start=True)
                    #startPlaying = self.sonos.play()
                    print("  Playing...")
                except:
                    print("  error starting to play...")

        if startPlaying == False:
            try:
                #startPlaying = self.sonos.play_from_queue(0, start=True)
                startPlaying = self.sonos.play()
                print("  Playing...")
            except:
                print("  error starting to play...")

        return True

    # this function gets called when a NFC tag is detected
    def play(self, entry):
        playItems = self.getPlayList(entry)

        # restart if last Tag is the same
        lastTag = self.lastTag()
        if not lastTag is None:
            theTimeDelta = datetime.now() - lastTag["scan"]
            print("time delta: " + str(theTimeDelta))
            if theTimeDelta < timedelta(seconds=self.restartTime):
                if entry['tag_id'] == lastTag["tag"]:
                    if self.restart():
                        return True

        self.unjoin()
        self.clearQueue()
        if entry['volume']:
            self.setMaxVolume(entry['volume'])

        if entry['type'] == "artist":
            self.playModeShuffleNoRepeat()
        elif entry['type'] == "genre":
            self.playModeShuffleNoRepeat()
        else:
            self.playModeNormal()

        self.playItems(playItems)
        if entry['time_offset']:
            self.setSkipTo(entry['time_offset'])

        self.setLastTag(entry['tag_id'])

        return True


    def lastTag(self):
        try:
            self.lastSavedTag
            print("last Tag found")
        except:
            print("last Tag not found")
            self.lastSavedTag = None
        return self.lastSavedTag



    def setLastTag(self, tag_uid):
        print("last Tag saved")
        self.lastSavedTag = {"tag" : tag_uid, "scan": datetime.now()}

    def saveLastTagTime(self):
        #only save when a track is playing
        try:
            transportInfo = self.sonos.get_current_transport_info()
            if transportInfo['current_transport_state'] == 'PLAYING':
                lastTag = self.lastTag()
                if not lastTag is None:
                    self.lastSavedTag = {"tag" : lastTag["tag"], "scan": datetime.now()}
                    print("last tag time saved")
                    return True
                else:
                    print("did not save last tag time")
                    return False
            else:
                print("music is currently not playing")
                return False
            return False
        except:
            return False


    def markUnknown(self, aTagUid):
        tag_uid = str(aTagUid)
        print("  No record for tag UID: " + tag_uid)
        aUnknownTag = {
        tag_uid: {'comment': 'last scan: ' + str(datetime.now()), 'title': '', 'vol': 1, 'time_offset': None,
                  'type': None, 'item': None}, }

        unknownFileName = self.settings + "/" + "2_unknown_Tags" + ".txt"
        if os.path.isfile(unknownFileName):
            unknownTagsJSON = open(unknownFileName)
            unknownTags = json.load(unknownTagsJSON)
            unknownTagsJSON.close()
        else:
            unknownTags = {}

        unknownTags.update(aUnknownTag)
        dump = json.dumps(unknownTags, sort_keys=True, indent=4, separators=(',', ': '))
        fobj_out = open(unknownFileName, "w")
        fobj_out.write(dump)
        fobj_out.close()


    # sonos methods

    def setSkipTo(self, time_offset=None):
        if time_offset:
            try:
                self.sonos.seek(time_offset)
                print("  Skipped to " + time_offset)
                return True
            except:
                return False
        return False

    def setMaxVolume(self, volModifier=1):
        self.setVolume(self.sonosVolume(), volModifier)
        return True

    def setVolume(self, newVolume, volModifier):
        print("  setting Volume to:" + str(newVolume))
        currentHour = time.localtime()[3]
        isNight = 0
        if currentHour < self.daytimeRange[0] or currentHour > self.daytimeRange[1]:  # is it nighttime?
            isNight = 1

        if isNight:
            maxVol = int(round(self.nightVol * volModifier, 0))
            if newVolume >= maxVol:
                self.setSonosVolume(maxVol)
                print("  " + str(newVolume) + " is to loud for Nighttime volume, setting it to " + str(maxVol))
            elif newVolume < maxVol:
                self.setSonosVolume(newVolume)

        else:
            maxVol = int(round(self.dayVol * volModifier, 0))
            if newVolume >= maxVol:
                self.setSonosVolume(maxVol)
                print("  " + str(newVolume) + " is to loud for Daytime volume, setting it to " + str(maxVol))
            elif newVolume < maxVol:
                self.setSonosVolume(newVolume)
        return True

    def setSonosVolume(self, volume):
        try:
            self.sonos.volume = volume
        except:
            print("some error")
        return True

    def sonosVolume(self):
        volume = 0
        try:
            volume = self.sonos.volume
        except:
            print("some error")
        return volume

    def volumeUp(self, numberOfSteps):
        newVolume = self.sonosVolume() + numberOfSteps
        self.setVolume(newVolume, 1)
        return True

    def togglePlayModeShuffle(self):
        try:
            if self.sonos.play_mode == 'SHUFFLE':
                self.sonos.play_mode = 'REPEAT_ALL'
                print("now: REPEAT_ALL")
            elif self.sonos.play_mode == 'REPEAT_ALL':
                self.sonos.play_mode = 'SHUFFLE'
                print("now: SHUFFLE")
            elif self.sonos.play_mode == 'NORMAL':
                self.sonos.play_mode = 'SHUFFLE_NOREPEAT'
                print("now: SHUFFLE_NOREPEAT")
            elif self.sonos.play_mode == 'SHUFFLE_NOREPEAT':
                self.sonos.play_mode = 'NORMAL'
                print("now: NORMAL")
            else:
                 self.sonos.play_mode = 'NORMAL'
                 print("now: NORMAL")
            return True
        except:
            return False

    def playModeNormal(self):
        try:
            print("do NORMAL")
            self.sonos.play_mode = 'NORMAL'
            return True
        except:
            return False

    def playModeRepeatAll(self):
        try:
            print("do REPEAT_ALL")
            self.sonos.play_mode = 'REPEAT_ALL'
            return True
        except:
            return False

    def playModeShuffle(self):
        try:
            print("do SHUFFLE")
            self.sonos.play_mode = 'SHUFFLE'
            return True
        except:
            return False

    def playModeShuffleNoRepeat(self):
        try:
            print("do SHUFFLE_NOREPEAT")
            self.sonos.play_mode = 'SHUFFLE_NOREPEAT'
            return True
        except:
            return False

    def clearQueue(self):
        if self.clear:
            try:
                self.sonos.clear_queue()
                return True
            except:
                return False
        return False

    def unjoin(self):
        if self.unjoinBool == True:
            try:
                self.sonos.unjoin()
                print("unjoined")
                return True
            except:
                return False
        return False

    def unjoinForced(self):
        try:
            self.sonos.unjoin()
            print("unjoined")
            return True
        except:
            return False

    def stop(self):
        try:
            self.sonos.stop()
            print("  Sonos stopped")
            return True
        except:
            return False


    def pause(self):
        try:
            self.sonos.pause()
            print("  Sonos paused")
            return True
        except:
            return False


    def next(self):
        try:
            self.sonos.next()
            print("  playing next track")
            return True
        except:
            return False


    def previous(self):
        try:
            self.sonos.previous()
            print("  playing previous track")
            return True
        except:
            return False


    def restart(self):
        try:
            self.sonos.play()
            print("  unpause()...")
            return True
        except:
            return False


    def playPause(self):
        try:
            transportInfo = self.sonos.get_current_transport_info()
            if transportInfo['current_transport_state'] == 'PLAYING':
                self.sonos.pause()
                print("  pause()...")
            elif transportInfo['current_transport_state'] == 'PAUSED_PLAYBACK':
                self.sonos.play()
                print("  play()...")
            elif transportInfo['current_transport_state'] == 'STOPPED':
                self.sonos.play()
                print("  play()... from start")
            else:
                self.sonos.play()
                print("  play()... from unknown state")
            return True
        except:
            return False


    def get_current_track_info(self):
        try:
            trackInfo = self.sonos.get_current_track_info()
            return trackInfo
        except:
            return {}
#!/usr/bin/env python
from __future__ import print_function

import json
import os.path
import time
from datetime import datetime, timedelta

from soco import SoCo
from soco.data_structures import *
import logging
logger = logging.getLogger('blocks')

class SonosController(object):
    def __init__(self, dayVol=25, nightVol=15, daytimeRange=None, unjoin=True, clear=True,
                 settingsFolder="settings", restartTime=10):
        if daytimeRange is None:
            daytimeRange = [7, 17]
        self.dayVol = dayVol
        self.nightVol = nightVol
        self.daytimeRange = daytimeRange
        self.unjoinBool = unjoin
        self.clear = clear
        self.settings = settingsFolder
        self.restartTime = restartTime
        self.sonosDevice = None
        self.lastSavedTag = None

    def startSonos(self, sonos_ip):
        if sonos_ip == "demo":
            self.sonosDevice = None
            logger.info("Using Sonos Demo...")
            return

        # Sonos setup
        logger.info("Connecting to Sonos...")
        #device = SoCo.discovery.any_soco()
        #self.sonosDevice = device.group.coordinator
        device = SoCo(sonos_ip)
        self.sonosDevice = device.group.coordinator
        logger.info("Connected to Sonos: " + self.sonosDevice.player_name)

        # Use this section to get the URIs of new songs we want to add
        info = self.get_current_track_info()
        logger.info("Currently Playing: " + info['title'])
        logger.info("URI: " + info['uri'])
        logger.info("---")
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

    def getCache(self, entry):
        playitems = self.loadPlayList(entry)
        return to_didl_string(*playitems)

    def getPlayList(self, entry):

        playitems = entry['playitems']
        if playitems and not playitems == '':
            return from_didl_string(playitems)
        else:
            return self.loadPlayList(entry)

    def loadPlayList(self, entry):
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

    @staticmethod
    def getUrlCache(entry):
        item = DidlResource(uri=entry['item'], protocol_info='*:*:*:*')
        return list([item])

    def getMusicLibraryInformationCache(self, searchType, entry, valueType):
        returnItems = list([])

        # noinspection PyUnusedLocal
        startItem = 0
        startAtIndex = 0
        while True:
            try:
                # self.music_library.get_music_library_information('albums', start, max_items, full_album_art_uri)
                playlist_info = self.sonosDevice.music_library.get_music_library_information(searchType,
                                                                                             start=startAtIndex,
                                                                                             max_items=100)
                returnedItems = playlist_info.number_returned
            except:
                logger.info("some error")
                break
            if returnedItems == 0:
                break
            if entry['type'] == valueType:
                for playlist in playlist_info:
                    playlistTitle = playlist.title
                    if playlistTitle == entry['item']:
                        logger.info('found ' + entry['item'])
                        try:
                            track_list = self.sonosDevice.music_library.browse(playlist)
                            returnItems.extend(track_list)
                        except:
                            logger.info("some error")
            startAtIndex += returnedItems

        # playlist_info = #sonos.music_library.get_music_library_information('sonos_playlists',search_term='Shovels And Rope')
        # logger.info('Fonud {} Sonos playlists'.format(playlist_info.number_returned))

        return returnItems

    def playItems(self, items):
        startPlaying = False

        for item in items:
            try:
                self.sonosDevice.add_to_queue(item)
            except:
                logger.info("  error adding...: " + sys.exc_info()[0])
            if startPlaying == False:
                try:
                    startPlaying = self.sonosDevice.play_from_queue(0, start=True)
                    # startPlaying = self.sonos.play()
                    logger.info("  Playing...")
                except:
                    logger.info("  error starting to play...")

        if startPlaying == False:
            try:
                # startPlaying = self.sonos.play_from_queue(0, start=True)
                # noinspection PyUnusedLocal
                startPlaying = self.sonosDevice.play()
                logger.info("  Playing...")
            except:
                logger.info("  error starting to play...")

        return True

    # this function gets called when a NFC tag is detected
    def play(self, entry):
        playItems = self.getPlayList(entry)

        # restart if last Tag is the same
        lastTag = self.lastTag()
        if not lastTag is None:
            theTimeDelta = datetime.now() - lastTag["scan"]
            logger.info("time delta: " + str(theTimeDelta))
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
            # noinspection PyUnusedLocal
            var = self.lastSavedTag
            logger.info("last Tag found")
        except:
            logger.info("last Tag not found")
            self.lastSavedTag = None
        return self.lastSavedTag

    def setLastTag(self, tag_uid):
        logger.info("last Tag saved")
        self.lastSavedTag = {"tag": tag_uid, "scan": datetime.now()}

    def saveLastTagTime(self):
        # only save when a track is playing
        try:
            transportInfo = self.sonosDevice.get_current_transport_info()
            if transportInfo['current_transport_state'] == 'PLAYING':
                lastTag = self.lastTag()
                if not lastTag is None:
                    self.lastSavedTag = {"tag": lastTag["tag"], "scan": datetime.now()}
                    logger.info("last tag time saved")
                    return True
                else:
                    logger.info("did not save last tag time")
                    return False
            else:
                logger.info("music is currently not playing")
                return False
        except:
            return False

    def markUnknown(self, aTagUid):
        tag_uid = str(aTagUid)
        logger.info("  No record for tag UID: " + tag_uid)
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
                self.sonosDevice.seek(time_offset)
                logger.info("  Skipped to " + time_offset)
                return True
            except:
                return False
        return False

    def setMaxVolume(self, volModifier=1):
        self.setVolume(self.sonosVolume(), volModifier)
        return True

    def setVolume(self, newVolume, volModifier):
        logger.info("  setting Volume to:" + str(newVolume))
        currentHour = time.localtime()[3]
        isNight = 0
        if currentHour < self.daytimeRange[0] or currentHour > self.daytimeRange[1]:  # is it nighttime?
            isNight = 1

        if isNight:
            maxVol = int(round(self.nightVol * volModifier, 0))
            if newVolume >= maxVol:
                self.setSonosVolume(maxVol)
                logger.info("  " + str(newVolume) + " is to loud for Nighttime volume, setting it to " + str(maxVol))
            elif newVolume < maxVol:
                self.setSonosVolume(newVolume)

        else:
            maxVol = int(round(self.dayVol * volModifier, 0))
            if newVolume >= maxVol:
                self.setSonosVolume(maxVol)
                logger.info("  " + str(newVolume) + " is to loud for Daytime volume, setting it to " + str(maxVol))
            elif newVolume < maxVol:
                self.setSonosVolume(newVolume)
        return True

    def setSonosVolume(self, volume):
        try:
            self.sonosDevice.volume = volume
        except:
            logger.info("some error")
        return True

    def sonosVolume(self):
        volume = 0
        try:
            volume = self.sonosDevice.volume
        except:
            logger.info("some error")
        return volume

    def volumeUp(self, numberOfSteps):
        newVolume = self.sonosVolume() + numberOfSteps
        self.setVolume(newVolume, 1)
        return True

    def togglePlayModeShuffle(self):
        try:
            if self.sonosDevice.play_mode == 'SHUFFLE':
                self.sonosDevice.play_mode = 'REPEAT_ALL'
                logger.info("now: REPEAT_ALL")
            elif self.sonosDevice.play_mode == 'REPEAT_ALL':
                self.sonosDevice.play_mode = 'SHUFFLE'
                logger.info("now: SHUFFLE")
            elif self.sonosDevice.play_mode == 'NORMAL':
                self.sonosDevice.play_mode = 'SHUFFLE_NOREPEAT'
                logger.info("now: SHUFFLE_NOREPEAT")
            elif self.sonosDevice.play_mode == 'SHUFFLE_NOREPEAT':
                self.sonosDevice.play_mode = 'NORMAL'
                logger.info("now: NORMAL")
            else:
                self.sonosDevice.play_mode = 'NORMAL'
                logger.info("now: NORMAL")
            return True
        except:
            return False

    def playModeNormal(self):
        try:
            logger.info("do NORMAL")
            self.sonosDevice.play_mode = 'NORMAL'
            return True
        except:
            return False

    def playModeRepeatAll(self):
        try:
            logger.info("do REPEAT_ALL")
            self.sonosDevice.play_mode = 'REPEAT_ALL'
            return True
        except:
            return False

    def playModeShuffle(self):
        try:
            logger.info("do SHUFFLE")
            self.sonosDevice.play_mode = 'SHUFFLE'
            return True
        except:
            return False

    def playModeShuffleNoRepeat(self):
        try:
            logger.info("do SHUFFLE_NOREPEAT")
            self.sonosDevice.play_mode = 'SHUFFLE_NOREPEAT'
            return True
        except:
            return False

    def clearQueue(self):
        if self.clear:
            try:
                self.sonosDevice.clear_queue()
                return True
            except:
                return False
        return False

    def unjoin(self):
        if self.unjoinBool:
            try:
                self.sonosDevice.unjoin()
                logger.info("unjoined")
                return True
            except:
                return False
        return False

    def unjoinForced(self):
        try:
            self.sonosDevice.unjoin()
            logger.info("unjoined")
            return True
        except:
            return False

    def stop(self):
        try:
            self.sonosDevice.stop()
            logger.info("  Sonos stopped")
            return True
        except:
            return False

    def pause(self):
        try:
            self.sonosDevice.pause()
            logger.info("  Sonos paused")
            return True
        except:
            return False

    def next(self):
        try:
            self.sonosDevice.next()
            logger.info("  playing next track")
            return True
        except:
            return False

    def previous(self):
        try:
            self.sonosDevice.previous()
            logger.info("  playing previous track")
            return True
        except:
            return False

    def restart(self):
        try:
            self.sonosDevice.play()
            logger.info("  unpause()...")
            return True
        except:
            return False

    def playPause(self):
        try:
            transportInfo = self.sonosDevice.get_current_transport_info()
            if transportInfo['current_transport_state'] == 'PLAYING':
                self.sonosDevice.pause()
                logger.info("  pause()...")
            elif transportInfo['current_transport_state'] == 'PAUSED_PLAYBACK':
                self.sonosDevice.play()
                logger.info("  play()...")
            elif transportInfo['current_transport_state'] == 'STOPPED':
                self.sonosDevice.play()
                logger.info("  play()... from start")
            else:
                self.sonosDevice.play()
                logger.info("  play()... from unknown state")
            return True
        except:
            return False

    def get_current_track_info(self):
        try:
            trackInfo = self.sonosDevice.get_current_track_info()
            return trackInfo
        except:
            return {}

# -*- coding: utf-8 -*-
import sys

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

from zvooq_radio import Radio
from zvooq_client import ZvooqkClient

from utils import create_track_list_item, log, notify


#---------------

def log(msg, level=xbmc.LOGWARNING):
    plugin = "[Radio Service]"
    xbmc.log("%s %s" % (plugin, msg), level)


class MyPlayer(xbmc.Player):
    def __init__(self, settings, playerCore=0):
        self.radio = None

        self.urls = []
        self.valid = True
        self.started = False
        self.settings = settings
        xbmc.Player.__init__(self, playerCore=playerCore)

    def start(self, station_id, station_from):
        log("Zvooq.Radio::start")
        self.radio = Radio(client, station_id, station_from, settings)
        self.radio.start_radio(self.__on_start)

    def __on_start(self, track, next_track):
        log("Zvooq.Radio::__on_start")
        self.add_next_track(track)
        self.add_next_track(next_track)
        self.play(pl, startpos=0)
        self.started = True

    def __on_play_next(self, track):
        log("Zvooq.Radio::__on_play_next")
        self.add_next_track(track)

    def queue_next(self):
        log("Zvooq.Radio::queue_next")
        self.radio.play_next(self.__on_play_next)

    def add_next_track(self, track):
        log("Zvooq.Radio::add_next_track")
        track, url = track
        li = create_track_list_item(settings, track)
        li.setPath(url)
        playIndex = pl.size()
        pl.add(url, li, playIndex)

        self.urls.append(url)

    def onPlayBackStopped(self):
        log("Zvooq.Radio::onPlayBackStopped")
        self.queue_next()

    def onQueueNextItem(self):
        log("Zvooq.Radio::onQueueNextItem")
        self.queue_next()

    def check(self):
        if not self.started:
            return

        try:
            url = self.getPlayingFile()
            self.valid = (url in self.urls) and pl.size() == len(self.urls)
            log("check valid: %s" % self.valid)
        except BaseException as ex:
            self.valid = False
            log("can't get current: %s" % ex)

#----------

# ??????????
def sendPlayTrack(client, track):
    if not track.duration_ms:
        return

    play_id = "1354-123-123123-124"
    album_id = track.albums[0].id if track.albums else 0
    from_ = "desktop_win-home-playlist_of_the_day-playlist-default"
    # client.play_audio(
    #   from_=from_,
    #   track_id=track.track_id,
    #   album_id=album_id,
    #   play_id=play_id,
    #   track_length_seconds=0,
    #   total_played_seconds=0,
    #   end_position_seconds=track.duration_ms / 1000,
    # )

    import threading
    t = threading.Thread(target=client.play_audio, kwargs={
        "from_": from_,
        "track_id": track.id,
        "album_id": album_id,
        "play_id": play_id,
        "track_length_seconds": int(track.duration_ms / 1000),
        "total_played_seconds": int(track.duration_ms / 1000),
        "end_position_seconds": int(track.duration_ms / 1000)
    })
    t.start()

    notify("Notify play", "play: " + track.title)
    pass


#------------

if __name__ == '__main__':
    log("Zvooq plugin player loaded ... (player)")

    settings = xbmcaddon.Addon("plugin.zvooq")

    token = settings.getSetting('token')
    high_res = bool(settings.getSettingBool('high_res'))
    if bool(settings.getSettingBool('big_fanart')):
        img_size = "800x800"
    else:
        img_size = "460x460"

    log(sys.argv)
    type_ = sys.argv[1]
    radio_type_ = sys.argv[2]
    station_key_ = sys.argv[3]

    # get stations info
    auth, client = check_login(settings)

    # init playlist
    pl = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
    pl.clear()

    # init player
    player = MyPlayer(settings, high_res = high_res)

    if type_ == "custom":
        player.start("%s:%s" % (radio_type_, station_key_), radio_type_)
    else:
        stations = zvooq_radio.make_structure(client)
        stations["dashboard"] = zvooq_radio.make_dashboard(client)
        station = stations[radio_type_][station_key_]
        player.start(station.getId(), station.source.station.id_for_from)


    monitor = xbmc.Monitor()

    while not monitor.abortRequested():
        player.check()
        if not player.valid:
            break
        # Sleep/wait for abort for 10 seconds
        if monitor.waitForAbort(10):
            # Abort was requested while waiting. We should exit
            break

    log("Stopped")
    del monitor
    del player
    del client


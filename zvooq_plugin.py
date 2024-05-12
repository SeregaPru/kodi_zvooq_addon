# coding=utf-8
import os
import sys
import urllib
from threading import Thread

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

import routing

sys.path.append("./")
sys.path.append(os.path.join(os.path.dirname(__file__), "lib/mutagen/"))

from zvooq_client import ZvooqkClient
from zvooq_player import sendPlayTrack
from zvooq_downloads import downloadTrack, downloadTracks, getTrackPath
from zvooq_radio import Radio

from utils import log, create_track_list_item, notify

#------------------

class Settings:
    prefixPath = ""
    imgSize = ""
    qualityIdx = ""
    qualityName = ""
    autoDownload = False

settings = Settings()

#------------------

settings_service = xbmcaddon.Addon("plugin.zvooq")
SERVICE_SCRIPT = "special://home/addons/plugin.zvooq/zvooq_service.py"

plugin = routing.Plugin()

client: ZvooqkClient = None

#------------------

def get_cover_img(uri):
    if not uri:
        return ""
    uri = uri.replace("{size}", settings.imgSize)
    if (not uri.startswith('http')):
        uri = "https://zvuk.com" + uri
    return uri

def AddItems(elements_type, elements, **params):
    xbmcplugin.setContent(addon_handle, elements_type)
    xbmcplugin.addDirectoryItems(addon_handle, elements, len(elements))
    xbmcplugin.endOfDirectory(addon_handle, **params)

def MakeListItem(label, img, playable = 'false'):
    li = xbmcgui.ListItem(label = label)
    li.setArt({"thumb": img, "icon": img, "fanart": img})
    li.setProperty('fanart_image', img)
    li.setProperty('IsPlayable', playable)
    return li


#-------- Радио ---------

    #if mode[0] == 'radio_station':
    #    radio_type = args["radio_type"][0]
    #    station_key = args["station_key"][0]
    #    url = "RunScript(%s, %s, %s, %s)" % (SERVICE_SCRIPT, 'radio', radio_type, station_key)
    #    log("Run radio with url: %s" % url)
    #    threading.Thread(target=xbmc.executebuiltin, args=(url,)).run()

def get_radio_group_name(key):
    return {
        'genre': "By Genre",
        'mood': "By Mood",
        'activity': "By Activity",
        'epoch': "By Epoch",
        'author': "By Author",
        'local': "By Place",
        'personal': "Personal",
    }.get(key, key)

def build_radio(client):
    dashboard = zvooq_radio.make_dashboard(client)
    elements = [build_item_radio_station(client, "dashboard", key, dashboard[key]) for key in dashboard.keys()]

    stations = zvooq_radio.make_structure(client)
    elements += [build_item_radio_type(key) for key in stations.keys()]

    xbmcplugin.addDirectoryItems(addon_handle, elements, len(elements))
    xbmcplugin.endOfDirectory(addon_handle)


def build_item_radio_station(client, radio_type, key, s_info):
    title = s_info.getTitle()
    img_url = s_info.getImage(settings.imgSize)
    background = s_info.getBackground()

    filename_src = settings.prefixPath + "rad_" + radio_type + "_" + key + ".png"
    ##!!filename = add_png_background(client, img_url, filename_src, background)

    li = xbmcgui.ListItem(label=title)
    li.setArt({"thumb": filename, "icon": filename, "fanart": filename})
    li.setProperty('fanart_image', filename)
    url = build_url({'mode': 'radio_station', 'title': title, "radio_type": radio_type, "station_key": key})
    return url, li, True


def build_item_radio_type(key):
    title = get_radio_group_name(key) + " ..."
    li = xbmcgui.ListItem(label=title)
    url = build_url({'mode': 'radio_type', 'title': title, "radio_type": key})
    return url, li, True


def build_radio_type(client, radio_type):
    stations = zvooq_radio.make_structure(client)[radio_type]
    elements = [build_item_radio_station(client, radio_type, key, stations[key]) for key in stations.keys()]

    xbmcplugin.addDirectoryItems(addon_handle, elements, len(elements))
    xbmcplugin.endOfDirectory(addon_handle)

#================

@plugin.route('/Search')
def build_Search():
    searchString = xbmcgui.Dialog().input("", type=xbmcgui.INPUT_ALPHANUM)
    if not searchString:
        return

    res = client.search(searchString)

    entry_list = []
    entry_list += [build_item_artist  ("/Artists",   artist,   "[Artist]  %s")   for artist in res["artists"] ]
    entry_list += [build_item_playlist("/Playlists", playlist, "[Playlist]  %s")   for playlist in res["playlists"] ]
    entry_list += [build_item_album   ("/Albums",    album,    "[Album]  %(artist)s - %(title)s (%(year)s) %(type)s")   for album in res["albums"] ]
    entry_list += [build_item_track   (              track,    "[Track]  %(title)s - %(artist)s")   for track in res["tracks"] ]

    AddItems('albums', entry_list)


#=========================
# разное скачивание

# скачать все треки
# byAlbums - раскладывать по альбомам (true) или класть все в одну папку (false)
def download_all(tracks, DestFolder):
    li = xbmcgui.ListItem()
    xbmcplugin.setResolvedUrl(addon_handle, False, listitem=li)

    t = Thread(target=downloadTracks, args=(client, tracks, DestFolder, settings))
    t.start()

# скачать все треки альбома
# GroupByArtist - (true) в папку с именем = исполнитель / альбом
#   либо все в папку альбома а исполнители допишутся в имена файлов
@plugin.route('/Download/Album/<album_id>')
def download_album(album_id):
    real_album_id = album_id[2:]
    album = client.albums_with_tracks(real_album_id)
    DestFolder = album.title if (album_id[0] == "f") else None
    download_all(album.tracks, DestFolder)


# скачать все треки плейлиста
# в одну папку с именем плейлиста, с именами файлов = имя_трека исполнитель
@plugin.route('/Download/Playlist/<playlist_id>')
def download_playlist(playlist_id):
    playlist = client.playlist_with_tracks(playlist_id)
    download_all(playlist.tracks, playlist.title)


# скачать избранные треки
# разложить по папкам с именем = исполнитель / альбом
def download_user_selected_tracks():
    download_all(client.users_likes_tracks(), None)


# скачать все треки артиста
# в папку с именем = исполнитель / альбом
def download_artist(client, artist_id):
    artist = client.artists([artist_id])[0]
    artist_tracks = client.artists_tracks(artist_id, page=0, page_size=artist.counts.tracks)
    download_all(artist_tracks.tracks, None)

#===========

# Play track
@plugin.route('/Track/<track_id>$')
def play_track(track_id):
    log("play_track: " + str(track_id));

    track = client.get_tracks([track_id])[0]
    downloaded, filePath, folder = getTrackPath(settings, track)

    path = filePath if downloaded else client.get_track_url(track, settings)
    #li = xbmcgui.ListItem(path=filePath if downloaded else client.get_track_url(track, settings) )
    li = create_track_list_item(settings, track, "%(title)s", path)
    xbmcplugin.setResolvedUrl(addon_handle, True, listitem=li)

    sendPlayTrack(client, track)

    if (not downloaded) and settings.autoDownload:
        t = Thread(target=downloadTrack, args=(client, track, None, settings))
        t.start()


#=================================================
# build routines

def build_url(query, base_url=None):
    if not base_url:
        base_url = sys.argv[0]
    return base_url + '?' + urllib.parse.urlencode(query, 'utf-8')

def build_url2(**query):
    return build_url(query)


def build_retry():
    li = xbmcgui.ListItem(label="Auth. error. Check token")
    url = build_url({'mode': None, 'title': "Auth. error. Check token"})
    elements = [(url, li, True), ]
    AddItems('songs', elements, updateListing=True, cacheToDisc=False)


@plugin.route('/UserCollection/Albums/<album_id>$')
@plugin.route('/UserCollection/Artists/<artist_id>/Albums/<album_id>$')
@plugin.route('/Artists/<artist_id>/Albums/<album_id>$')
@plugin.route('/Albums/<album_id>$')
def build_album(album_id, artist_id=0):
    log("[build_album] " + str(album_id))

    album = client.albums_with_tracks(album_id)

    xbmcplugin.setProperty(addon_handle, 'FolderName', album.title)
    AddItems('songs', [build_item_track(track)   for track in album.tracks] )


@plugin.route('/UserCollection/Playlists/<playlist_id>$')
@plugin.route('/Playlists/<playlist_id>$')
def build_playlist(playlist_id):
    log("[build_playlist] " + str(playlist_id))

    playlist = client.playlist_with_tracks(playlist_id)

    xbmcplugin.setProperty(addon_handle, 'FolderName', playlist.title)
    AddItems('songs', [build_item_track(track, "%(title)s - %(artist)s")   for track in playlist.tracks],  cacheToDisc=False)

    ###if playlist.tracks:
    ###    play_track(playlist.tracks[0].id)
        #sendPlayTrack(client, playlist.tracks[0])


# хак чтоб в веб морде идти назад через 2 папки
@plugin.route('/UserCollection/Artists/<artist_id>/Albums/$')
@plugin.route('/UserCollection/Artists/<artist_id>/Albums$')
@plugin.route('/Artists/<artist_id>/Albums/$')
@plugin.route('/Artists/<artist_id>/Albums$')
def back_albums(artist_id):
    log("[GO BACK FROM ALBUMS]")
    url = plugin.url_for_path(plugin.path[:-7])
    li = xbmcgui.ListItem(label = "<< BACK")
    AddItems('songs', [ (url, li, True) ] )


@plugin.route('/UserCollection/Artists/<artist_id>$')
@plugin.route('/Artists/<artist_id>$')
def build_artist(artist_id):
    log("[build_playlist] " + str(artist_id))

    albums = client.get_artist_info(artist_id)
    AddItems('albums', [build_item_album(plugin.path + "/Albums", album, "%(title)s (%(year)s) %(type)s")   for album in albums] )


# формирует пункт списка - трек. листовой, при клике - запуск плея
def build_menu_track(li, track):
    commands = []
    commands.append(( 'Stream From Track', "RunScript(%s, %s, %s, %s)" % (SERVICE_SCRIPT, 'custom', 'track', track.id)  ))

    if track.albums:
        album = track.albums[0]
        commands.append(( 'Go To Album',  'Container.Update(%s)' %  plugin.url_for_path('/Albums/' + str(album.id)),  ))
    if track.artists:
        artist = track.artists[0]
        commands.append(( 'Go To Artist', 'Container.Update(%s)' % plugin.url_for_path('/Artists/' + str(artist.id)), ))
    if commands:
        li.addContextMenuItems(commands)


def build_item_track(track, titleFormat="%(title)s"):
    log("[build_item_track] " + str(track.id))
    downloaded, filepath, folder = getTrackPath(settings, track)

    if downloaded:
        url = filepath
    else:
        url = plugin.url_for_path("/Track/" + str(track.id)) 
    li = create_track_list_item(settings, track, titleFormat)
    build_menu_track(li, track)

    return url, li, False


def build_item_artist(path, artist, titleFormat="%s"):
    log("[build_item_artist]")

    li = MakeListItem( titleFormat % artist.title, get_cover_img(artist.cover_uri))
    li.setInfo("music", {"artist":artist.title})
    url = plugin.url_for_path(path + "/" + str(artist.id)) 

    li.addContextMenuItems([
        ( 'Stream From Artist',  "RunScript(%s, %s, %s, %s)" % (SERVICE_SCRIPT, 'custom', 'artist', artist.id)     ),
        ( 'Download all tracks', 'Container.Update(%s)' % build_url2(mode='download_artist', artist_id=artist.id), )
    ])

    return url, li, True


def build_item_album(path, album, titleFormat="%(title)s"):
    log("[build_item_album] ")

    if album.cover_uri:
        img_url = get_cover_img(album.cover_uri)
    elif album.artists and album.artists[0].cover_uri:
        img_url = get_cover_img(album.artists[0].cover_uri)
    else:
        img_url = ""

    artist = ""
    if (album.artists): artist = album.artists[0]["title"]

    albumType = ""
    if (album.type): albumType = "[" + album.type + "]"

    li = MakeListItem( titleFormat % {"title":album.title, "artist":artist, "year":album.year, "type":albumType},  img_url, 'true')
    li.setInfo("music", {'album': album.title, "artist":artist, "year":album.year})
    url = plugin.url_for_path(path + "/" + str(album.id))

    li.addContextMenuItems([
        ( 'Stream From Album',   "RunScript(%s, %s, %s, %s)" % (SERVICE_SCRIPT, 'custom', 'album', album.id)       ),
        ( 'Download tracks (in folder)',    'Container.Update(%s)' % plugin.url_for(download_album, "f-" + album.id) ),
        ( 'Download tracks (artist/album)', 'Container.Update(%s)' % plugin.url_for(download_album, "a-" + album.id) ),
    ])
    if (album.artists):
        li.addContextMenuItems([
            ( 'Go To Artist', 'Container.Update(%s)' % plugin.url_for_path('/Artists/' + str(album.artists[0].id))  )
        ])

    return url, li, True


def build_item_playlist(path, playlist, titleFormat="%s"):
    log("[build_item_playlist] " + str(playlist.id))

    li = MakeListItem( titleFormat % playlist.title, get_cover_img(playlist.cover_uri), 'true')
    li.setInfo("music", {'album': playlist.title})
    url = plugin.url_for_path(path + "/" + str(playlist.id))     

    li.addContextMenuItems([(
        'Download tracks (playlist)', 'Container.Update(%s)' % plugin.url_for(download_playlist, playlist.id)
    )])

    return url, li, True


#-------- Жанры и настроения ---------
   
@plugin.route('/Playlists')
def build_main_playlists():
    genres_playlists = client.main_playlists()
    AddItems('playlists', [build_item_playlist("/Playlists", playlist, "%s") for playlist in genres_playlists] )

@plugin.route('/Genres')
def build_main_genres_moods():
    genres = client.genres_moods()
    AddItems('playlists', [build_item_playlist("/Genres", genre, "%s") for genre in genres] )

@plugin.route('/Genres/<genre_id>$')
def build_genre(genre_id):
    log("[build_genre] " + str(genre_id))

    playlist = client.genre_tracks(genre_id)

    xbmcplugin.setProperty(addon_handle, 'FolderName', playlist.title)
    AddItems('songs', [build_item_track(track, "%(title)s - %(artist)s")   for track in playlist.tracks],  cacheToDisc=False)


#-------- Избранное ---------

# избранные треки
@plugin.route('/UserCollection/Tracks')
def build_UserCollection_Tracks():
    tracks = client.users_likes_tracks()
    AddItems('songs', [build_item_track(track, "%(title)s - %(artist)s")  for track in tracks] )


# избранные плейлисты
@plugin.route('/UserCollection/Playlists')
def build_UserCollection_Playlists():
    like_playlists = client.users_likes_playlists()
    AddItems('playlists', [build_item_playlist(plugin.path, playlist, "%s") for playlist in like_playlists] )


# избранные альбомы
@plugin.route('/UserCollection/Albums')
def build_UserCollection_Albums():
    like_albums = client.users_likes_albums()
    AddItems('albums', [build_item_album(plugin.path, album, "%(artist)s - %(title)s")   for album in like_albums] )


# избранные артисты
@plugin.route('/UserCollection/Artists')
def build_UserCollection_Artists():
    like_artists = client.users_likes_artists()
    AddItems('artists', [build_item_artist('/UserCollection/Artists', artist, "%s")   for artist in like_artists] )


# главное меню - коллекция (избранное)
@plugin.route('/UserCollection')
def build_UserCollection():
    elements = []

    # Show [user likes] item
    li = MakeListItem("Треки", "special://home/addons/plugin.zvooq/assets/playlist.png", 'true')
    url = plugin.url_for(build_UserCollection_Tracks)
    li.addContextMenuItems([(
        'Download all',  'Container.Update(%s)' % build_url2(mode='download_user_selected_tracks'),
    )])
    elements.append((url, li, True))

    # Пункт - подменю - избранные плейлисты
    li = MakeListItem("Плейлисты ...", "special://home/addons/plugin.zvooq/assets/like_playlist.png")
    url = plugin.url_for(build_UserCollection_Playlists)
    elements.append((url, li, True))

    # Пункт - подменю - избранные альбомы
    li = MakeListItem("Альбомы ...", "special://home/addons/plugin.zvooq/assets/like_albums.png")
    url = plugin.url_for(build_UserCollection_Albums)
    elements.append((url, li, True))

    # Пункт - подменю - избранные артисты
    li = MakeListItem("Артисты ...", "special://home/addons/plugin.zvooq/assets/like_artists.png")
    url = plugin.url_for(build_UserCollection_Artists)
    elements.append((url, li, True))

    AddItems('', elements)


#==================================

#??TODO пока непонятно что это, потом разобраться
def updateStatus(client):
    def do_update(cl):
        #!!! TODO !!!
        #cl.account_status()
        #cl.account_experiments()
        #cl.settings()
        #cl.permission_alerts()
        pass

    Thread(target=do_update, args=(client,)).start()


# формируем меню 1-го уровня
def build_main():
    entry_list = []
    if client:
        # Search menu item
        li = MakeListItem("Поиск", "special://home/addons/plugin.zvooq/assets/search.png")
        url = plugin.url_for(build_Search)
        entry_list.append((url, li, True))

        # Show User Collection
        li = MakeListItem("Моя коллекция", "special://home/addons/plugin.zvooq/assets/collections.png")
        url = plugin.url_for(build_UserCollection)
        entry_list.append((url, li, True))

        li = MakeListItem("Жанры и настроения", "special://home/addons/plugin.zvooq/assets/genres.png")
        url = plugin.url_for(build_main_genres_moods)
        entry_list.append((url, li, True))

        li = MakeListItem("Плейлисты", "special://home/addons/plugin.zvooq/assets/playlists.png")
        url = plugin.url_for(build_main_playlists)
        entry_list.append((url, li, True))

    else:
        li = xbmcgui.ListItem(label="Login")
        url = plugin.url_for(build_login)
        entry_list.append((url, li, True))

    AddItems('', entry_list,   updateListing=True, cacheToDisc=False)


# формируем меню для не авторизованых
@plugin.route('/Login')
def build_login():
    pass


#==================================

def checkSettings():
    folder = settings_service.getSetting('folder')
    if not folder:
        dialogType = 3  # ShowAndGetWriteableDirectory
        heading = "Select download folder"
        while not folder:
            folder = xbmcgui.Dialog().browseSingle(dialogType, heading, "music", defaultt=folder)
        settings_service.setSetting('folder', folder)


# инициализируем клиент звука
# и проверяем наличие токена
def initClient(settings): 
    token = settings.getSetting('token')

    z = ZvooqkClient()
    z.set_token(token)
    log("!!! zvooq client initialized !!!")
    return (True, z)


@plugin.route('/')
def plugin_main():
    global client, authorized

    # Stop Radio script on any change
    # xbmc.executebuiltin("StopScript(%s)" % SERVICE_SCRIPT)

    #args = urllib.parse.parse_qs(sys.argv[2][1:])

    if client:
        updateStatus(client)
    build_main()
    return

#==================================

if __name__ == '__main__':
    log("Zvooq plugin loaded ... (main)")

    #-------

    checkSettings()
    settings.prefixPath = settings_service.getSetting('folder')

    settings.autoDownload = bool(settings_service.getSettingBool('auto_download'))

    if bool(settings_service.getSettingBool('big_fanart')):
        settings.imgSize = "800x800"
    else:
        settings.imgSize = "460x460"

    settings.qualityIdx = settings_service.getSettingInt('quality')
    settings.qualityName = ("SQ", "HQ", "HiFi")[settings.qualityIdx]
    log("quality: %s" % settings.qualityName)

    #-------

    addon_handle = int(sys.argv[1])
    xbmcplugin.setContent(addon_handle, 'songs')

    try:
        authorized, client = initClient(settings_service)
    except Exception as ex:
        log("Zvooq client initialization error: " + str(ex))
        build_retry()
        #return

    log(" ")
    log(plugin.path)
    plugin.run()

    #plugin_main()

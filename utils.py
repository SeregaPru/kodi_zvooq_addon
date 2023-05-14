import xbmc
import xbmcgui


def create_track_list_item(settings, track, titleFormat="%(title)s", path=""):
    log("  > > > " + str(track))

    album  = track.albums  and track.albums[0]
    artist = track.artists and track.artists[0]
    if track.cover_uri:
        img_url = track.cover_uri.replace("{size}", settings.imgSize)
    elif album and album.cover_uri:
        img_url = album.cover_uri.replace("{size}", settings.imgSize)
    #elif artist and artist.cover:
    #    cover = artist.cover
    #    img_url = "https://%s" % ((cover.uri or cover.items_uri[0]).replace("{size}", img_size))
    else:
        img_url = ""

    #label = titleFormat % f"{artist.title} - {track.title}" if artist and show_artist else track.title
    label = titleFormat % {"title":track.title, "artist":artist.title}
    label2 = f"{album.title} ({str(album.year)})" if album else ""

    li = xbmcgui.ListItem(label=label, label2=label2, path=path, offscreen=False)
    li.setProperty('IsPlayable', 'true')

    li.setArt({
        "thumb": img_url,
        "icon": img_url,
        "fanart": img_url,
        "poster": img_url,
        "banner": img_url,
        "clearart": img_url,
        "clearlogo": img_url,
        "landscape": img_url,
    })

    info = {
        "title": track.title,
        "mediatype": "song",
        # "lyrics": "(On a dark desert highway...)"
        # "rating": 10,  # 1-10
        # "userrating": 10,  # 1-10
        # "playcount": 0,
        # "lastplayed": "",  # Y-m-d h:m:s = 2009-04-05 23:16:04
        # "dbid": 0,  # Only add this for items of the local db. You also need to set the correct 'mediatype'!
        # "comment": "This is a great song"
    }
    if track.duration_ms:
        info["duration"] = int(track.duration_ms / 1000)
    if artist:
        info["artist"] = artist.title
    if album:
        info["album"] = album.title
        if album.track_position:
            info["tracknumber"] = str(album.track_position)
            info["discnumber"]  = str(album.track_position) ###???TODO
        info["year"] = str(album.year)
        info["genre"] = album.genre
    li.setInfo("music", info)
    return li


def getArtistCover(artist):
    if artist.cover:
        return artist.cover.download, "artist_%s.jpg" % artist.id

def getAlbumCover(album):
    if album.cover_uri:
        return album.download_cover, "album_%s.jpg" % album.id
    return getArtistCover(album.artists[0])

def getTrackCover(track):
    if track.cover_uri:
        return track.download_cover, "track_%s.jpg" % track.trackId
    return getAlbumCover(track.albums[0])

def getPlaylistCover(playlist):
    if playlist.cover:
        return playlist.cover.download, "playlist_%s_%s.jpg" % (playlist.playlistId, playlist.uid)
    return None


def notify(title, msg:str, duration=1):
    xbmc.executebuiltin("Notification(%s,%s,%s)" % (legalize(title), legalize(msg), duration))


def log(msg: str, level=xbmc.LOGWARNING):
    plugin = "---"
    xbmc.log("[%s] %s" % (plugin, legalize(msg)), level)


def legalize(value):
    return value



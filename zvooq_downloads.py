import os
import time
import requests
import platform

from mutagen import mp3, easyid3
from mutagen.flac import FLAC, Picture

from lib.zvooq_api import Album, Artist, Playlist, Track, Service
from utils import log, notify


_EXCLUDED = ':/?|;.<>*"'

#----------------------

plt = platform.system()

def fixWindows(path):
    return path

def fixLinux(path):
    return path.encode("utf-8")

fixPath = fixWindows if plt == "Windows" else fixLinux


def existsPath(path):
    return os.path.exists(fixPath(path))


def checkAndMakeFolder(path):
    if not existsPath(path):
        os.makedirs(fixPath(path))
    return path


#  возвращает триаду - название, альбом, артист
def _trackSimpleData(track):
    artist = "".join([c for c in track.artists[0]["title"] if c not in _EXCLUDED]) if track.artists else ""
    album  = "".join([c for c in track.albums [0]["title"] if c not in _EXCLUDED]) if track.albums  else ""
    title = track.title
    return title, album, artist


def getTrackFolders(settings, track):
    title, album, artist = _trackSimpleData(track)

    folderArtist = os.path.join(settings.prefixPath, artist)
    folderAlbum  = (folderArtist + "/" + album) if album else ""

    return folderAlbum, folderArtist


def get_filename(track, qualityIdx=0):
    title, album, artist = _trackSimpleData(track)
    title = "".join(["_" if c in _EXCLUDED else c for c in title])
    exts = ["mp3", "mp3", "flac"]
    return "%s.%s" % (title, exts[qualityIdx])


# return (file exist, file full path, folder)
def getTrackPath(settings, track):
    title, album, artist = _trackSimpleData(track)
    if album:
        folder = "%s/%s" % (artist, album)
    else:
        folder = artist
    folder = os.path.join(settings.prefixPath, folder)

    f = get_filename(track, settings.qualityIdx)
    path = os.path.join(folder, f)
    return existsPath(path), os.path.normpath(path), folder

#----------------------

# return:
#  codec, bitrate_in_kbps
def get_track_download_info(client, track, settings):
    dInfo = sorted([d for d in client.get_download_info(track)], key=lambda x: x.bitrate_in_kbps)
    log("Quality: %s, dInfo: %s" % (settings.qualityName, len(dInfo)))
    if (len(dInfo) < settings.qualityIdx):
        return dInfo[-1]
    else:
        return dInfo[settings.qualityIdx]


def downloadTrack(client, track: Track, settings):
    log("[downloadTrack] " + str(track.id));

    downloaded, path, folder = getTrackPath(settings, track)
    if not downloaded:
        checkAndMakeFolder(folder)

        url = client.get_track_url(track, settings)
        path = fixPath(path)

        r = requests.get(url, allow_redirects=True, verify=True)
        open(path, 'wb').write(r.content)

        if settings.qualityIdx < 2: # mp3
            addFileMetadataMP3(track, path)
        else: # codec = flac
            addFileMetadataFLAC(track, path)

        #-- download images
        albumFolder, artistFolder = getTrackFolders(settings, track)

        # download album cover
        #folder.jpg
        if albumFolder:
            albumImg = fixPath(albumFolder) + "/folder.jpg"
            album = track.albums and track.albums[0]
            if album and album.cover_uri and (not existsPath(albumImg)):
                album_img_url = album.cover_uri.replace("{size}", settings.imgSize)
                download_image(album_img_url, albumImg)

        # download artist image
        #artist-poster.jpg
        artistImg = fixPath(artistFolder) + "/artist-poster.jpg"
        artist = track.artists and track.artists[0]
        if artist and artist.cover_uri and (not existsPath(artistImg)):
            artist_img_url = artist.cover_uri.replace("{size}", settings.imgSize)
            download_image(artist_img_url, artistImg)

    notify("Download", "Done: %s" % path, 1)
    return path


def downloadTracks(client, tracks, settings):
    log("[downloadTrackS] " + str(tracks));

    notify("Download", "Download %s files" % len(tracks), 5)
    [downloadTrack(client, track, settings) for track in tracks]
    notify("Download", "All files downloaded.", 5)

#---

def addFileMetadataFLAC(track: Track, path):
    audio = FLAC(path)
    audio["TRACK_ID"] = str(track.id)
    audio["TITLE"] = track.title
    if track.artists:
        audio["ARTIST"] = track.artists[0].title
    if track.albums:
        audio["ALBUM"] = track.albums[0].title
        audio["TRACKNUMBER"] = str(track.albums[0].track_position)
        ##audio["TRACKTOTAL"] = str(releases["tracktotal"])
        ###audio["GENRE"] = track.albums[0].genre
        ##audio["COPYRIGHT"] = releases["copyright"]
        audio["DATE"] = str(track.albums[0].year)
        audio["YEAR"] = str(track.albums[0].year)[0:4]
        audio["RELEASE_ID"] = str(track.albums[0].id)

    audio.save()
    time.sleep(1)


def addFileMetadataMP3(track: Track, path):
    audio = mp3.MP3(path, ID3=easyid3.EasyID3)
    audio["title"] = track.title
    audio["length"] = str(track.duration_ms)
    if track.artists:
        audio["artist"] = track.artists[0].title
    if track.albums:
        audio["album"] = track.albums[0].title
        audio["tracknumber"] = str(track.albums[0].track_position.index)
        audio["date"] = str(track.albums[0].year)
        audio["genre"] = track.albums[0].genre
    audio.save()
    time.sleep(1)


def download_image(url, path):
    r = requests.get(url, allow_redirects=True, verify=True)
    open(path, 'wb').write(r.content)

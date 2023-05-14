import glob
import os
import sys
import subprocess
import time
from datetime import datetime
from pathlib import Path
from shutil import copyfile
import re
import requests
import json

from typing import Callable, Dict, List, Optional, Union

from utils import log

from mutagen.flac import FLAC, Picture

from lib.zvooq_api import Album, Artist, Playlist, Track, Service


class ZvooqkClient:
    def __init__(self):
        self.Service = Service()
        pass

    def set_token(self, token):
        self.Service.set_token(token)

#------------------

    # album
    def albums_with_tracks(self, album_id):
        return self.Service.getReleaseInfo(album_id)

    # playlist
    def playlist_with_tracks(self, playlist_id):
        return self.Service.getPlaylistInfo(playlist_id)

    # формирует список альбомов для артиста
    def get_artist_info(self, artist_id):
        return self.Service.getArtistInfo(artist_id)

    # get tracks info
    def get_tracks(self, track_ids):
        return self.Service.getTracks(track_ids)

    # возвращает ссылку на УРЛ трека
    def get_track_url(self, track, settings):
        return self.Service.getTrackLink([track.id], settings.qualityIdx)[track.id]


#------------------
# user likes ...

    # формирует список избранных альбомов
    # .. вызываем метод получения избранных альбомов с сервера и формирует список объектов
    def users_likes_albums(self):
        return self.Service.getLikesAlbums()

    # получает с сервера список избранных треков
    def users_likes_tracks(self):
        return self.Service.getLikesTracks()

    # получает с сервера список избранных артистов
    def users_likes_artists(self):
        return self.Service.getLikesArtists()

    # получает с сервера список избранных плейлистов
    def users_likes_playlists(self):
        return self.Service.getLikesPlaylists()

#====================

    # поиск
    def search(self, searchString):
        res = self.Service.Search(searchString)
        return res

    # жанры и настроения
    def genres_moods(self):
        res = self.Service.getGenresMoodsPlaylists()
        return res
    
    # плейлисты на 1й странице
    def main_playlists(self):
        res = self.Service.getMainPlaylists()
        return res


#========
    def play_audio(
        self,
        from_: str,
        track_id: Union[str, int],
        album_id: Union[str, int],
        play_id: str = None,

        track_length_seconds: int = 0,
        total_played_seconds: int = 0,
        end_position_seconds: int = 0,

        playlist_id: str = None,
        from_cache: bool = False,
        uid: int = None,
        timestamp: str = None,
        client_now: str = None,
        timeout: Union[int, float] = None,
        *args,
        **kwargs,
    ) -> bool:
        """Метод для отправки текущего состояния прослушиваемого трека.

        Args:
            track_id (:obj:`str` | :obj:`int`): Уникальный идентификатор трека.
            from_ (:obj:`str`): Наименования клиента с которого происходит прослушивание.
            album_id (:obj:`str` | :obj:`int`): Уникальный идентификатор альбома.
            playlist_id (:obj:`str`, optional): Уникальный идентификатор плейлиста, если таковой прослушивается.
            from_cache (:obj:`bool`, optional): Проигрывается ли трек с кеша.
            play_id (:obj:`str`, optional): Уникальный идентификатор проигрывания.
            uid (:obj:`int`, optional): Уникальный идентификатор пользователя.
            timestamp (:obj:`str`, optional): Текущая дата и время в ISO.
            track_length_seconds (:obj:`int`, optional): Продолжительность трека в секундах.
            total_played_seconds (:obj:`int`, optional): Сколько было всего воспроизведено трека в секундах.
            end_position_seconds (:obj:`int`, optional): Окончательное значение воспроизведенных секунд.
            client_now (:obj:`str`, optional): Текущая дата и время клиента в ISO.
            timeout (:obj:`int` | :obj:`float`, optional): Если это значение указано, используется как время ожидания
                ответа от сервера вместо указанного при создании пула.
            **kwargs (:obj:`dict`, optional): Произвольные аргументы (будут переданы в запрос).

        Returns:
            :obj:`bool`: :obj:`True` при успешном выполнении запроса, иначе :obj:`False`.

        Raises:
            :class:`yandex_music.exceptions.YandexMusicError`: Базовое исключение библиотеки.
        """

        """
        if uid is None and self.me is not None:
            uid = self.me.account.uid

        url = f'{self.base_url}/play-audio'

        data = {
            'track-id': track_id,
            'from-cache': from_cache,
            'from': from_,
            'play-id': play_id or '',
            'uid': uid,
            'timestamp': timestamp or f'{datetime.now().isoformat()}Z',
            'track-length-seconds': track_length_seconds,
            'total-played-seconds': total_played_seconds,
            'end-position-seconds': end_position_seconds,
            'album-id': album_id,
            'playlist-id': playlist_id,
            'client-now': client_now or f'{datetime.now().isoformat()}Z',
        }

        result = self._request.post(url, data, timeout=timeout, *args, **kwargs)

        return result == 'ok'
        """
        return True

#====================

    def __ntfs(self, filename):
        for ch in ['<', '>', ':', '"', '/', '\\', '|', '?', '*']:
            if ch in filename:
                filename = filename.replace(ch, " ")
        filename = " ".join(filename.split())
        filename = filename.replace(" .flac", ".flac")
        return filename

    def __launch(self, args):
        try:
            pipe = subprocess.Popen(args, creationflags=0x08000000, stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            output, err = pipe.communicate()
            pipe.wait()

            if pipe.returncode != 0:
                print(args + '\n')
                print(output + '\n')
                print(err)
                raise Exception("Unable to launch")
            return output
        except FileNotFoundError:
            return("Install pingo and imagemagick!")


    def __to_str(self, l):
        if isinstance(l, int):
            return [l]
        elif not isinstance(l, str):
            l = [str(int) for int in l]
            l = ",".join(l)
            l = str(l.strip('[]'))
        return l

    def __get_copyright(self, label_ids):
        label_ids = self.__to_str(label_ids)
        url = f"https://zvuk.com/api/tiny/labels"
        params = {
            "ids": label_ids
        }
        r = requests.get(url, params=params, verify=self.verify)
        self.printResp(r)

        resp = r.json(strict=False)

        info = {}
        for i in resp['result']['labels'].values():
            info[i["id"]] = i['title']
        return(info)

    def __get_tracks_metadata(self, track_ids):
        track_ids = self.__to_str(track_ids)
        params = {
            "ids": track_ids
        }
        url = "https://zvuk.com/api/tiny/tracks"
        r = requests.get(url, params=params,
                         headers=self.headers, verify=self.verify)
        self.printResp(r)

        resp = r.json(strict=False)
        info = {}
        for s in resp['result']['tracks'].values():
            if s['has_flac']:
                author = s['credits']
                name = s['title']
                album = s['release_title']
                release_id = s['release_id']
                track_id = s['id']
                if s['genres']:
                    #genre = s['genres'][0]
                    genre = ", ".join(s['genres'])
                else:
                    genre = ""

                number = s["position"]
                image = s['image']['src'].replace(r"&size={size}&ext=jpg", "")

                info[track_id] = {"author": author, "name": name, "album": album, "release_id": release_id,
                                  "track_id": track_id, "genre": genre, "number": number, "image": image}
            else:
                if s['highest_quality'] != "flac":
                    raise Exception(
                        "has_flac, but highest_quality is not flac, token is invalid")
                raise Exception(f"Skipping track {s['title']}, no flac")
        return info



    def __get_artists_info(self, artist_ids):
        artist_ids = self.__to_str(artist_ids)

        info = {}
        url = "https://zvuk.com/api/tiny/artists"
        params = {
            "ids": artist_ids
        }
        r = requests.get(url, params=params,
                         headers=self.headers, verify=self.verify)
        self.printResp(r)

        url = "https://zvuk.com/api/tiny/releases"
        params = {
            "artist": artist_ids
        }
        r = requests.get(url, params=params,
                         headers=self.headers, verify=self.verify)
        self.printResp(r)

        resp = r.json(strict=False)

        labels = set()
        for i in resp['result']["releases"].values():
            labels.add(i["label_id"])
        labels_info = self.__get_copyright(labels)

        # print(resp)
        for a in resp['result']["releases"].values():
            info[a["id"]] = {"track_ids": a["track_ids"], "tracktotal": len(a["track_ids"]), "copyright": labels_info[a['label_id']], "date": a["date"], "album": a["title"], "author": a["credits"]}

        return info

    def __download_image(self, release_id, image_link):
        pic = Path(f"temp_{release_id}.jpg")
        comp_pic = Path(f"temp_{release_id}_comp.jpg")
        if not pic.is_file():
            r = requests.get(image_link, allow_redirects=True,
                             verify=self.verify)
            open(pic, 'wb').write(r.content)
            print(self.__launch(f'pingo -sa -notime -strip {pic}'))
            if os.path.getsize(pic) > 2 * 1000 * 1000:
                print(self.__launch(f"magick convert {pic} -define jpeg:extent=1MB {comp_pic}"))
                print(self.__launch(f'pingo -sa -notime -strip {comp_pic}'))
            else:
                copyfile(pic, comp_pic)

            # pingo optimize, compress
        return {"original": pic, "compressed": comp_pic}

    def __save_track(self, url, metadata, releases, single):
        pic = self.__download_image(metadata["release_id"], metadata["image"])

        if not single and releases["tracktotal"] != 1:
            folder = f'{releases["author"]} - {releases["album"]} ({str(releases["date"])[0:4]})'
            folder = self.__ntfs(folder)
            if not os.path.exists(folder):
                os.makedirs(folder)
                copyfile(pic["original"], os.path.join(folder, "cover.jpg"))
            # else:
            #    print("Folder already exist, continue?")
            #    a = input()
            #    if not a:
            #        os._exit()
            # os.chdir(folder)
            pic = pic["compressed"]
            filename = f'{metadata["number"]:02d} - {metadata["name"]}.flac'
        else:
            pic = pic["original"]
            folder = ""
            filename = f'{metadata["author"]} - {metadata["name"]}.flac'

        filename = self.__ntfs(filename)
        filename = os.path.join(folder, filename)

        r = requests.get(url, allow_redirects=True, verify=self.verify)
        open(filename, 'wb').write(r.content)

        audio = FLAC(filename)
        audio["ARTIST"] = metadata["author"]
        audio["TITLE"] = metadata["name"]
        audio["ALBUM"] = metadata["album"]
        audio["TRACKNUMBER"] = str(metadata["number"])
        audio["TRACKTOTAL"] = str(releases["tracktotal"])

        audio["GENRE"] = metadata["genre"]
        audio["COPYRIGHT"] = releases["copyright"]
        audio["DATE"] = str(releases["date"])
        audio["YEAR"] = str(releases["date"])[0:4]

        audio["RELEASE_ID"] = str(metadata["release_id"])
        audio["TRACK_ID"] = str(metadata["track_id"])

        covart = Picture()
        covart.data = open(pic, 'rb').read()
        covart.type = 3  # as the front cover
        covart.mime = "image/jpeg"
        audio.add_picture(covart)

        # Printing the metadata
        print(audio.pprint() + '\n')

        # Saving the changes
        audio.save()
        time.sleep(1)


    def download_tracks(self, track_ids, single=False, releases=""):
        metadata = self.__get_tracks_metadata(track_ids)
        link = self.__get_tracks_link(track_ids)

        if len(metadata) != len(link):
            raise Exception("metadata != link")

        if not releases:
            release_ids = set()
            for i in metadata.values():
                release_ids.add(i["release_id"])
            releases = self.__get_releases_info(release_ids)

        for i in metadata.keys():
            self.__save_track(link[i], metadata[i],
                              releases[metadata[i]["release_id"]], single)

    def download_albums(self, release_ids):
        track_ids = []
        releases = self.__get_releases_info(release_ids)
        for i in releases.values():
            track_ids = i["track_ids"]
            self.download_tracks(track_ids, releases=releases)

    def download_artist(self, artist_ids):
        artists = self.__get_artists_info(artist_ids)
        track_ids = []
        for i in artists.values():
            track_ids += i["track_ids"]
        self.download_tracks(track_ids, releases=releases)


    def parse_file(self, filename):
        track_ids = []
        release_ids = []

        # read file to string
        print ("read file ...")
        text_file = open(filename, "r", encoding="utf-8")
        data = text_file.read()
        text_file.close()

        # regesp string - look for releases
        print ("find releases ...")
        pattern = r'\/release\/([0-9]+)'
        release_ids = re.findall(pattern, data)
        release_ids = list(dict.fromkeys(release_ids)) # remove duplicates
        print (release_ids)
        return release_ids


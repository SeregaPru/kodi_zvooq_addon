import glob
import os
import subprocess
import sys
import time
from pathlib import Path
from shutil import copyfile
import re
import requests
import json

from utils import log
from lib.zvooq_api import Album, Artist, Playlist, Track


class Service:

    root = "https://zvuk.com"

    def __init__(self):
        self.verify = True
        self.headers = []
        pass

#---------------
# debug & logging

    def printResp(self, r):
        log("")
        log("  / - - - r e q u e s t - -")
        log(" | code | " + str(r.status_code))
        log(" | resn | " + str(r.reason))
        log(" | text | " + r.text)
        log("  \ - - - - - - - - - - - -")

        ####r.raise_for_status()

    def __to_str(self, l):
        if isinstance(l, int):
            return [l]
        elif not isinstance(l, str):
            l = [str(int) for int in l]
            l = ",".join(l)
            l = str(l.strip('[]'))
        return l

#---------------
# network service methods

    def set_token(self, token):
        if len(token) != 32:
            raise Exception("Wrong token length")
        self.headers = {"x-auth-token": token}


    def sendGrapql(self, data):
        url = self.root + "/api/v1/graphql"

        reqHeaders = self.headers
        reqHeaders["content-type"] = "application/json"
        reqHeaders["apollographql-client-name"] ="SberZvuk"
        reqHeaders["apollographql-client-version"] ="1.3"

        log(json.dumps(data))
        try:
            r = requests.post(url, data=json.dumps(data), headers=reqHeaders, verify=self.verify)
        except Exception as err:
            log(" Exception ===========")
            log(err)

        self.printResp(r)

        resp = r.json(strict=False)
        return resp


    def sendGet(self, url, params):
        r = requests.get(url, params=params,
                         headers=self.headers, verify=self.verify)
        self.printResp(r)

        resp = r.json(strict=False)
        return resp

#---------------
# Likes

    # получает список любимых альбомов,
    # отправляет запрос на сервер
    def getLikesAlbums(self):
        data = {
            "operationName": "userCollection",
            "variables": {},
            "query": " ".join( """query userCollection {\n collection {\n 
                    releases {\n id\n title\n date\n 
                      image {\n src\n }\n  
                      artists {\n id\n title\n }\n  
                    }\n }\n } """.split() )
        }
        resp = self.sendGrapql(data)

        res = []
        for rel in resp['data']["collection"]["releases"]:
            artists = []
            for art in rel["artists"]:
                artists.append(Artist(
                    id    = art["id"],
                    title = art["title"],
                ))            

            alb = Album(
                id      = rel["id"],
                title   = rel["title"],
                date    = rel["date"],
                cover_uri = rel["image"]["src"],
                artists = artists,
            )
            res.append(alb)

        return res


    # получает список любимых плейлистов,
    # отправляет запрос на сервер
    def getLikesPlaylists(self):
        data = {
            "operationName": "userCollection",
            "variables": {},
            "query": " ".join( """query userCollection {\n collection {\n 
                    playlists {\n id\n title\n
                      image {\n src\n }\n  
                    }\n }\n } """.split() )
        }
        resp = self.sendGrapql(data)

        res = []
        for pl in resp['data']["collection"]["playlists"]:
            pls = Playlist(
                id = pl["id"],
                title = pl["title"],
                cover_uri = pl["image"]["src"],
            )
            res.append(pls)

        return res
    

    # получает список любимых артистов,
    # отправляет запрос на сервер
    def getLikesArtists(self):
        data = {
            "operationName": "userCollection",
            "variables": {},
            "query": " ".join( """query userCollection {\n collection {\n 
                    artists {\n id\n title\n
                      image {\n src\n }\n  
                    }\n }\n } """.split() )
        }
        resp = self.sendGrapql(data)

        res = []
        for a in resp['data']["collection"]["artists"]:
            art = Artist(
                id = a["id"],
                title = a["title"],
                cover_uri = a["image"]["src"],
            )
            res.append(art)

        return res


    # получает список любимых треков,
    # отправляет запрос на сервер
    def getLikesTracks(self):
        data = {
            "operationName": "userCollection",
            "variables": {},
            "query": " ".join( """query userCollection {\n collection {\n 
                    tracks {\n id\n title\n
                      duration\n
                      position\n
                      release {\n id\n title\n date\n  image {\n src\n }\n  }\n  
                      artists {\n id\n title\n }\n  
                    }\n }\n } """.split() )
        }
        resp = self.sendGrapql(data)

        res = []
        for tr in resp['data']["collection"]["tracks"]:
            ar = []
            for a in tr["artists"]:
                ar.append(Artist(
                    id    = a["id"],
                    title = a["title"],
                ))            

            rel = tr["release"]
            al = [ Album(
                id    = rel["id"],
                title = rel["title"],
                date  = rel["date"],
                cover_uri = rel["image"]["src"],
                track_position = tr["position"],
            ) ]

            trk = Track(
                id        = tr["id"],
                title     = tr["title"],
                albums    = al,
                artists   = ar,
                duration_ms = tr["duration"] * 1000,
            )
            res.append(trk)

        return res

#----

    # жанры и настроения - список плейлистов
    def getGenresMoodsPlaylists(self):
        url = self.root + "/_next/data/release-17.0.0/genres.json"
        resp = self.sendGet(url, [])
        genres = resp['pageProps']['genresAndMoods']

        playlists = []
        for pl in genres:
            if pl["mood"] == False:
                pls = Playlist(
                    id    = pl["id"],
                    title = pl["title"],
                    cover_uri = pl["image"]["src"],
                )
                playlists.append(pls)

        for pl in genres:
            if pl["mood"] == True:
                pls = Playlist(
                    id    = pl["id"],
                    title = pl["title"],
                    cover_uri = pl["image"]["src"],
                )
                playlists.append(pls)

        return playlists


    # плейлисты на 1й странице
    def getMainPlaylists(self):
        url = self.root + "/_next/data/release-17.0.0/playlists.json"
        resp = self.sendGet(url, [])
        resppls = resp['pageProps']['playlists']

        playlists = []
        for pl in resppls:
            pls = Playlist(
                id    = pl["id"],
                title = pl["title"],
                cover_uri = pl["image"]["src"],
            )
            playlists.append(pls)

        return playlists

#----

    # информация по заданному альбому 
    def getReleaseInfo(self, release_id):
        data = {
            "operationName": "getReleases",
            "variables": { 
                "ids": [release_id]
            },
            "query": " ".join( """query getReleases($ids: [ID!]!) {\n getReleases(ids: $ids) {\n
                id\n title\n date\n   
                tracks {\n
                    id\n  title\n
                    duration\n
                    position\n
                }\n    
                image {\n src\n }\n  
                artists {\n id\n title\n }\n
            }\n } """.split() )
        }
        resp = self.sendGrapql(data)

        rel = resp['data']["getReleases"][0]

        artiss = []
        for ar in rel["artists"]:
            artiss.append(Artist(
                id    = ar["id"],
                title = ar["title"],
            ))            

        alb_int = Album(
            id    = rel["id"],
            title = rel["title"],
            date  = rel["date"],
        )

        tracs = []
        for tr in rel["tracks"]:
            if tr == None: continue
            tracs.append(Track(
                id    = tr["id"],
                title = tr["title"],
                duration_ms = tr["duration"] * 1000,
                cover_uri = rel["image"]["src"],
                artists = artiss,
                albums = [alb_int],
            ))            

        album = Album(
            id = rel["id"],
            title = rel["title"],
            date = rel["date"],
            cover_uri = rel["image"]["src"],
            artists = artiss,            
            tracks = tracs
        )

        return album


    # информация по заданному плейлисту 
    def getPlaylistInfo(self, playlist_id):
        data = {
            "operationName": "getPlaylists",
            "variables": { 
                "ids": [playlist_id]
            },
            "query": " ".join( """query getPlaylists($ids: [ID!]!) {\n getPlaylists(ids: $ids) {\n
                id\n title\n 
                image {\n src\n }\n  
                tracks {\n
                    id\n  title\n
                    duration\n
                    position\n                    
                    artists {\n id\n title\n }\n
                    release {\n id\n title\n date\n    image {\n src\n }\n    }\n  
                }\n    
            }\n } """.split() )
        }
        resp = self.sendGrapql(data)

        pl = resp['data']["getPlaylists"][0]

        trcs = []
        for tr in pl["tracks"]:
            rel = tr["release"]
            alb_int = Album(
                id    = rel["id"],
                title = rel["title"],
                date  = rel["date"],
                cover_uri = rel["image"]["src"],
                track_position = tr["position"],
            )

            art_s = []
            for art in tr["artists"]:
                art_s.append(Artist(
                    id    = art["id"],
                    title = art["title"],
                ))            

            trcs.append(Track(
                id    = tr["id"],
                title = tr["title"],
                duration_ms = tr["duration"] * 1000,
                artists = art_s,
                albums = [alb_int],
                ##cover_uri = res["image"]["src"],
            ))            

        pls = Playlist(
            id    = pl["id"],
            title = pl["title"],
            cover_uri = pl["image"]["src"],
            tracks = trcs
        )

        return pls


    # информация по заданному артисту
    def getArtistInfo(self, artist_id):
        data = {
            "operationName": "getArtists",
            "variables": { 
                "ids": [artist_id]
            },
            "query": " ".join( """query getArtists($ids: [ID!]!) {\n getArtists(ids: $ids) {\n
                id\n title\n 
                image {\n src\n }\n
                releases {\n
                    id\n  title\n date\n  type\n
                    artists {\n id\n title\n }\n
                    image {\n src\n }\n
                }\n  
            }\n } """.split() )
        }
        resp = self.sendGrapql(data)

        albumTypes = {"album":None, "single":"Single", "deluxe":"Deluxe"}

        art = resp['data']["getArtists"][0]

        albs = []
        for rel in art["releases"]:
            art_s = []
            for rel_art in rel["artists"]:
                art_s.append(Artist(
                    id    = rel_art["id"],
                    title = rel_art["title"],
                ))            

            alb = Album(
                id      = rel["id"],
                title   = rel["title"],
                date    = rel["date"],
                cover_uri = rel["image"]["src"],
                type = albumTypes.get(rel["type"], None),
                artists = art_s,
            )
            albs.append(alb)

        return albs


    # информация по заданныму трекам 
    def getTracks(self, track_ids):
        data = {
            "operationName": "getTracks",
            "variables": { 
                "ids": track_ids
            },
            "query": " ".join( """query getTracks($ids: [ID!]!) {\n getTracks(ids: $ids) {\n
                id\n  title\n
                duration\n
                position\n
                hasFlac\n  
                artists {\n id\n title\n }\n
                release {\n id\n title\n date\n    image {\n src\n }\n    }\n  
            }\n } """.split() )
        }
        resp = self.sendGrapql(data)

        tracks = resp['data']["getTracks"]

        res = []
        for tr in tracks:
            rel = tr["release"]
            alb_int = Album(
                id    = rel["id"],
                title = rel["title"],
                date  = rel["date"],
                cover_uri = rel["image"]["src"],
                track_position = tr["position"],
            )

            art_s = []
            for art in tr["artists"]:
                art_s.append(Artist(
                    id    = art["id"],
                    title = art["title"],
                ))            

            trk = Track(
                id        = tr["id"],
                title     = tr["title"],
                duration_ms = tr["duration"] * 1000,
                artists   = art_s,
                albums    = [alb_int],

                hasFlac = tr["hasFlac"],
            )
            res.append(trk)

        return res

#---------------

    # поиск
    def Search(self, searchString):
        data = {
            "operationName": "search",
            "variables": { 
                "limit": 6,
                "query": searchString
            },
            "query": " ".join( """query search(
                $query: String, 
                $limit: Int = 2, 
            ) {\n  search(query: $query) {\n    
                searchId\n

                releases(limit: $limit) {\n
                    score\n      
                    items {\n id\n title\n date\n type\n
                        searchTitle\n availability\n
                        artists {\n  id\n title\n  }\n        
                        image {\n  src\n }\n
                    }\n
                }\n

                artists(limit: $limit) {\n      
                    score\n 
                    items {\n  id\n  title\n        
                        searchTitle\n  description\n        
                        image {\n  src\n  }\n
                    }\n    
                }\n

                playlists(limit: $limit)  {\n      
                    score\n      
                    items {\n   id\n  title\n        
                        isPublic\n   description\n   duration\n        
                        image {\n  src\n  }\n
                    }\n    
                }\n

                tracks(limit: $limit) {\n
                    score\n      
                    items {\n id\n title\n  position\n duration\n
                        artists {\n  id\n  title\n  }\n        
            			release {\n  id\n  title\n          
			            	image {\n src\n  }\n
			            }\n      
                    }\n
                }\n
                
            }\n  }\n """.split() )
        }
        resp = self.sendGrapql(data)

        src = resp['data']["search"]

        tracks = []
        if "tracks" in src:
            for tr in src["tracks"]["items"]:
                rel = tr["release"]
                al = [ Album(
                    id        = rel["id"],
                    title     = rel["title"],
                    cover_uri = rel["image"]["src"],
                    track_position = tr["position"],
                ) ]

                ar = tr["artists"][0]
                art = Artist(
                    id      = ar["id"],
                    title   = ar["title"],
                )

                trk = Track(
                    id        = tr["id"],
                    title     = tr["title"],
                    duration_ms = tr["duration"] * 1000,
                    albums    = al,
                    artists = [art],
                    #hasFlac = tr["hasFlac"],
                )
                tracks.append(trk)

        albumTypes = {"album":None, "single":"Single", "deluxe":"Deluxe"}
        albs = []
        if "releases" in src:
            for rel in src["releases"]["items"]:
                ar = rel["artists"][0]
                art = Artist(
                    id   = ar["id"],
                    title = ar["title"],
                )
                alb = Album(
                    id      = rel["id"],
                    title   = rel["title"],
                    date    = rel["date"],
                    cover_uri = rel["image"]["src"],
                    artists = [art],
                    type = albumTypes.get(rel["type"], None),

                )
                albs.append(alb)

        artists = []
        if "artists" in src:
            for ar in src["artists"]["items"]:
                art = Artist(
                    id      = ar["id"],
                    title   = ar["title"],
                    cover_uri = ar["image"]["src"],
                )
                artists.append(art)

        playlists = []
        if "playlists" in src:
            for pl in src["playlists"]["items"]:
                pls = Playlist(
                    id        = pl["id"],
                    title     = pl["title"],
                    cover_uri = pl["image"]["src"],
                )
                playlists.append(pls)

        res = {}
        res["tracks"] = tracks
        res["albums"] = albs
        res["artists"] = artists
        res["playlists"] = playlists
        return res

#---------------

    # возвращает ссылки на УРЛ треков
    def getTrackLink(self, track_ids, qualityIdx):
        qs = ["mid", "high", "flac"]

        links = {}
        for i in track_ids:
            url = self.root + "/api/tiny/track/stream"
            params = {
                "id": i,
                "quality": qs[qualityIdx]
            }
            resp = self.sendGet(url, params)

            links[i] = resp['result']['stream']
            time.sleep(1)
        return links

    

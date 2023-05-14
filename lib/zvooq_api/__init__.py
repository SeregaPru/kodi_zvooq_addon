__version__ = '1.0.0'
__license__ = 'GNU Lesser General Public License v3 (LGPLv3)'
__copyright__ = 'Copyright (C)'


from .base import ZvooqObject

from .album.album import Album
from .artist.artist import Artist
from .playlist.playlist import Playlist
from .track.track import Track

from .service import Service


__all__ = [
    'Album',
    'Artist',
    'Playlist',
    'Track',
    'ZvooqObject',

    'Service',

]

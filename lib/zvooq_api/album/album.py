from typing import TYPE_CHECKING, Optional, List, Union

from ...zvooq_api  import ZvooqObject


class Album(ZvooqObject):
    """Класс, представляющий альбом.

    Note:
        ---

    Attributes:
        id (:obj:`int`): Идентификатор альбома.
        title (:obj:`str`): Название альбома.
        artists (:obj:`list` из :obj:`zvooq_api.Artist`): Артисты.
        cover_uri (:obj:`str`): Ссылка на обложку.
        date (:obj:`str`): дата
        year (:obj:`int`): Год релиза.
        track_position (:obj:`int`): Номер трека в алюбоме, передается при передаче одного трека
        genre (:obj:`str`): Жанр музыки.
        tracks (:obj:`list` из :obj:`Tracks`): Треки.
        type (:obj:`str`): тип - сингл...

    Args:
        id (:obj:`int`, optional): Идентификатор альбома.
        title (:obj:`str`, optional): Название альбома.
        artists (:obj:`list` из :obj:`zvooq_api.Artist`, optional): Артисты.
        cover_uri (:obj:`str`, optional): Ссылка на обложку.
        date (:obj:`str`): дата
        year (:obj:`int`): Год релиза.
        track_position (:obj:`int`): Номер трека в алюбоме, передается при передаче одного трека
        genre (:obj:`str`): Жанр музыки.
        tracks (:obj:`list` из :obj:`Tracks`): Треки.
        type (:obj:`str`): тип - сингл...
    """

    def __init__(
        self,
        id: Optional[int] = None,
        title: Optional[str] = None,
        artists: List['Artist'] = None,
        cover_uri: Optional[str] = None,
        date: Optional[int] = None,
        track_position: Optional[int] = None,
        genre: Optional[str] = None,
        tracks: List['Track'] = None,
        type: Optional[str] = None,

        #client: Optional['Client'] = None,
        **kwargs,
    ) -> None:
        self.id = id
        self.title = title
        self.artists = artists
        self.cover_uri = cover_uri
        self.date = date
        self.track_position = track_position
        self.genre = genre
        self.tracks = tracks
        self.type = type

        self.year = str(date)[:4] #!!TODO

        #self.client = client

        ##TODO super().handle_unknown_kwargs(self, **kwargs)


from typing import TYPE_CHECKING, Optional, List, Union

from ...zvooq_api  import ZvooqObject, Artist, Album


class Track(ZvooqObject):
    """Класс, представляющий трек.

    Note:
        ---

    Attributes:
        id (:obj:`int`): Идентификатор трек.
        title (:obj:`str`): Название трек.
        artists (:obj:`list` из :obj:`zvooq_api.Artist`): Артисты.
        albums (:obj:`list` из :obj:`zvooq_api.Album`): Артисты.
        cover_uri (:obj:`str`): Ссылка на обложку.
        duration_ms (:obj:`int`): длительность в милисек
        hasFlac(:obj:`int`): 

    Args:
        id (:obj:`int`, optional): Идентификатор трек.
        title (:obj:`str`, optional): Название трек.
        artists (:obj:`list` из :obj:`zvooq_api.Artist`, optional): Артисты.
        albums (:obj:`list` из :obj:`zvooq_api.Album`): Артисты.
        cover_uri (:obj:`str`, optional): Ссылка на обложку.
        duration_ms (:obj:`int`): длительность в милисек
        hasFlac(:obj:`int`): 
    """

    def __init__(
        self,
        id: Optional[int] = None,
        title: Optional[str] = None,
        artists: List['Artist'] = None,
        albums: List['Album'] = None,
        cover_uri: Optional[str] = None,
        duration_ms: Optional[int] = None,
        hasFlac: Optional[int] = 0,

        #client: Optional['Client'] = None,
        **kwargs,
    ) -> None:
        self.id = id
        self.title = title
        self.artists = artists
        self.albums = albums
        self.cover_uri = cover_uri

        self.duration_ms = duration_ms
        self.hasFlac = hasFlac

        #self.client = client

        ##TODO super().handle_unknown_kwargs(self, **kwargs)

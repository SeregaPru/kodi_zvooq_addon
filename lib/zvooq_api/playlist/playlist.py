from typing import TYPE_CHECKING, Optional, List, Union

from ...zvooq_api  import ZvooqObject


class Playlist(ZvooqObject):
    """Класс, представляющий плейлист.

    Note:
        ---

    Attributes:
        id (:obj:`int`): Идентификатор плейлист.
        title (:obj:`str`): Название плейлист.
        cover_uri (:obj:`str`): Ссылка на обложку.
        tracks (:obj:`list` из :obj:`Tracks`): Треки.

    Args:
        id (:obj:`int`, optional): Идентификатор плейлист.
        title (:obj:`str`, optional): Название плейлист.
        cover_uri (:obj:`str`, optional): Ссылка на обложку.
        tracks (:obj:`list` из :obj:`Tracks`): Треки.
    """

    def __init__(
        self,
        id: Optional[int] = None,
        title: Optional[str] = None,
        cover_uri: Optional[str] = None,
        tracks: List['Track'] = None,

        #client: Optional['Client'] = None,
        **kwargs,
    ) -> None:
        self.id = id
        self.title = title
        self.cover_uri = cover_uri
        self.tracks = tracks

        #self.client = client

        ##TODO super().handle_unknown_kwargs(self, **kwargs)


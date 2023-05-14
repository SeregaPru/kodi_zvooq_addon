from typing import TYPE_CHECKING, Optional, List, Union

from ...zvooq_api  import ZvooqObject



class Artist(ZvooqObject):
    """Класс, представляющий альбом.

    Note:
        ---

    Attributes:
        id (:obj:`int`): Идентификатор альбома.
        title (:obj:`str`): Название альбома.
        cover_uri (:obj:`str`, optional): Ссылка на обложку.

    Args:
        id (:obj:`int`, optional): Идентификатор альбома.
        title (:obj:`str`, optional): Название альбома.
        cover_uri (:obj:`str`, optional): Ссылка на обложку.
    """

    def __init__(
        self,
        id: Optional[int] = None,
        title: Optional[str] = None,
        cover_uri: Optional[str] = None,

        #client: Optional['Client'] = None,
        **kwargs,
    ) -> None:
        self.id = id
        self.title = title
        self.cover_uri = cover_uri

        #self.client = client

        ##TODO super().handle_unknown_kwargs(self, **kwargs)


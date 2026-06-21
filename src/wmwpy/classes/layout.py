from ..gameobject import GameObject
from ..utils.filesystem import *
from .widget import get_widget


class Layout(GameObject):

    def __init__(
        self,
        file: str | bytes | File = None,
        filesystem: Filesystem | Folder = None,
        gamepath: str = None,
        assets: str = '/assets',
        baseassets: str = '/',
    ) -> None:
        super().__init__(filesystem, gamepath, assets, baseassets)

        self.filename = ''

        get_widget('test').widget

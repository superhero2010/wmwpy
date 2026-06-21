from .texturesettings import TextureSettings
from ..gameobject import GameObject
from ..utils.filesystem import File, Filesystem, Folder
from ..utils.textures import getHDFile
from ..utils.waltex import Waltex

from PIL import Image

import io
import os


class Texture(GameObject):

    def __init__(
        self,
        image: Image.Image | Waltex | File,
        filesystem: Filesystem | Folder = None,
        gamepath: str = None,
        assets: str = '/assets',
        baseassets: str = '/',
        HD = False,
        TabHD = False,
    ) -> None:
        """Texture for image.
        Args:
            image (Image.Image | Waltex | File): Image object. Can be PIL.Image.Image, Waltex image, or file.
            filesystem (Filesystem | Folder, optional): Filesystem to use. Defaults to None.
            gamepath (str, optional): Game path. Only used if filesystem not specified. Defaults to None.
            assets (str, optional): Assets path relative to game path. Only used if filesystem not specified. Defaults to '/assets'.
            baseassets (str, optional): Base assets path within the assets folder, e.g. `/perry/` in wmp. Defaults to `/`.
            HD (bool, optional): Use HD image. Defaults to False.
            TabHD (bool, optional): Use TabHD image. Defaults to False.
        Raises:
            TypeError: image must be PIL.Image.Image, Waltex, or filesystem.File.
        """
        super().__init__(filesystem, gamepath, assets, baseassets)

        self._file = image
        self.HD = HD
        self.TabHD = TabHD

        if isinstance(self._file, (File, str)):
            if isinstance(self._file, str):
                self.filename = self._file
            else:
                self.filename = self._file.path

            self._file = getHDFile(
                self._file,
                HD = self.HD,
                TabHD = self.TabHD,
                filesystem = self.filesystem,
                gamepath = self.gamepath,
                assets = self.assets,
                baseassets = self.baseassets,
            )
        else:
            self.filename = ''

        if isinstance(self._file, str):
            self._file = self.filesystem.get(self._file)

        if isinstance(self._file, Waltex):
            self.image = self._file.image
        elif isinstance(self._file, Image.Image):
            self.image = self._file
        elif isinstance(self._file, File):
            self.image = self._file.read()
            if isinstance(self.image, Waltex):
                self.image = self.image.image
        elif isinstance(self._file, str):
            self._file = self.filesystem.get(self._file)
            self.image = self._file.read()
        else:
            raise TypeError(
                'image must be PIL.Image.Image, Waltex, or filesystem.File.'
            )

        # self._textureSettings = TextureSettings(
        #     filesystem = self.filesystem,
        #     gamepath = self.gamepath,
        #     assets = self.assets,
        #     baseassets = self.baseassets,
        # )

        # self.textureSettings = self._textureSettings.get(self.filename)

        # if not self.textureSettings.premultiplyAlpha:
        #     self.image = self.image.convert('RGBa')

    @property
    def size(self) -> tuple[int, int]:
        """The size of the image.
        Returns:
            tuple[int,int]: (width,height)
        """
        return self.image.size

    def save(self, filename: str = None) -> File:
        """Save the image to the filesystem.
        Args:
            filename (str, optional): Path to save the image to. Defaults to None.
        Returns:
            File: wmwpy File object.
        """
        if filename == None:
            filename = self.filename
        else:
            self.filename = filename

        fileio = io.BytesIO()

        self.image.save(fileio, format = os.path.splitext(filename)[1][1:].upper())

        file = self.filesystem.add(filename, fileio, replace = True)

        return file

    def show(self, *args, **kwargs):
        """Calls the PIL.Image.Image.show() method.
        
        ---
        #### Description copied from the PIL library
        
        Displays this image. This method is mainly intended for debugging purposes.

        This method calls PIL.ImageShow.show internally. You can use
        PIL.ImageShow.register to override its default behavior.

        The image is first saved to a temporary file. By default, it will be in PNG format.

        On Unix, the image is then opened using the **display**, **eog** or **xv** utility, depending on which one can be found.

        On macOS, the image is opened with the native Preview application.

        On Windows, the image is opened with the standard PNG display utility.

        Args:
            title (str | None, optional): Optional title to use for the image window, where possible.. Defaults to None.
        """
        return self.image.show(*args, **kwargs)

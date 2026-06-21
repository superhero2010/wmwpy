from .texture import Texture
from ..utils.textures import getHDFile, HDFile
from ..utils.filesystem import *
from ..utils.path import joinPath
from ..gameobject import GameObject

import numpy
import PIL.Image
from lxml import etree
from copy import deepcopy

import io
import os


class Imagelist(GameObject):
    TEMPLATE = b"""<?xml version="1.0"?>
    <ImageList imgSize="512 512" file="" textureBasePath="/Textures/">
    </ImageList>
    """

    class Format():
        IMAGELIST = 0
        PAGES = 1

    def __init__(
        self,
        file: str | bytes | File = None,
        filesystem: Filesystem | Folder = None,
        gamepath: str = None,
        assets: str = '/assets',
        baseassets: str = '/',
        HD: bool = False,
        TabHD: bool = False,
        save_images: bool = False
    ) -> None:
        """Get imagelist from file
        
        Args:
            file (str | bytes | File, optional): File to read. Defaults to None.
            filesystem (Filesystem | Folder, optional): Filesystem to use. Defaults to None.
            gamepath (str, optional): Game path. Only used if filesystem not specified. Defaults to None.
            assets (str, optional): Assets path relative to game path. Only used if filesystem not specified. Defaults to '/assets'.
            baseassets (str, optional): Base assets path within the assets folder, e.g. `/perry/` in wmp. Defaults to `/`.
            HD (bool, optional): Use HD images. Defaults to False.
            TabHD (bool, optional): Use TabHD images. Defaults to False.
            save_images (bool, optional): Save images in filesystem. Note: this may take more time to load the imagelist. Defaults to False.
        
        Raises:
            FileNotFoundError: Filesystem is not usable and no gamepath.
        """

        super().__init__(filesystem, gamepath, assets, baseassets)

        self.HD = HD
        self.TabHD = TabHD

        if isinstance(file, str):
            self.filename = file
            newFile = HDFile(
                file,
                HD = self.HD,
                TabHD = self.TabHD,
                filesystem = self.filesystem,
                gamepath = self.gamepath,
                assets = self.assets,
                baseassets = self.baseassets,
            )

            file = newFile.filename
            self.HD = newFile.HD
            self.TabHD = newFile.TabHD
        elif isinstance(file, File):
            self.filename = file.path
            newFile = HDFile(
                file.path,
                HD = self.HD,
                TabHD = self.TabHD,
                filesystem = self.filesystem,
                gamepath = self.gamepath,
                assets = self.assets,
                baseassets = self.baseassets,
            )

            file = newFile.filename
            self.HD = newFile.HD
            self.TabHD = newFile.TabHD
        else:
            self.filename = ''

        if isinstance(file, str):
            file = self.filesystem.get(file)

        self.file = super().get_file(file, template = self.TEMPLATE)

        if isinstance(self.file, io.BytesIO):
            self.file.seek(0)

        self.xml: etree.ElementBase = etree.parse(self.file).getroot()

        self.pages: list[Imagelist.Page] = []
        self.format = self.Format.IMAGELIST

        # self.images = {}

        self.read(save_images = save_images)

    def read(self, save_images: bool = False):
        """Read the imagelist xml.

        Args:
            save_images (bool, optional): Save images in filesystem. Note: this may take more time to load the imagelist. Defaults to False.
        """
        self.format = self.Format.IMAGELIST

        for element in self.xml:
            if element is etree.Comment:
                continue

            if element.tag == 'Page':
                self.format = self.Format.PAGES
                page = self.Page(
                    element,
                    filesystem = self.filesystem,
                    HD = self.HD,
                    TabHD = self.TabHD,
                    save_images = save_images,
                )

                self.pages.append(page)

        if self.format == self.Format.IMAGELIST:
            page = self.Page(
                self.xml,
                filesystem = self.filesystem,
                HD = self.HD,
                TabHD = self.TabHD,
                save_images = save_images,
            )

            self.pages.append(page)

    def update(self, gap: tuple[int, int] = (1, 1), auto_fit = False):
        """Update the atlas image.

        Args:
            gap (tuple[int,int], optional): The gap between images. Defaults to (1,1).
            auto_fit (bool, optional): Auto minimize the atlas image size while keeping all the sprites in the image. Defaults to False.
        """
        for page in self.pages:
            page.update(gap = gap, auto_fit = auto_fit)

    def export(
        self,
        path: str = None,
        exportImage: bool = True,
        format: str = 'webp',
        removeImageFiles: bool = True,
    ):
        """Export the xml of the imagelist.

        Args:
            path (str, optional): Path to the file in the filesystem to write to. If `None`, it will not save to a file, only report the output. Defaults to None.
            exportImage (bool, optional): Whether to also export the atlas image(s). If there are multiple pages, it'll append `_split_#` to the end of the filenames. Defaults to False.
            imageFormat (str, optional): What format to export the images as. Defaults to 'webp'.
            removeImageFiles (bool, optional): Remove image files from filesystem. Defaults to False.

        Raises:
            TypeError: Path is an existing folder.

        Returns:
            bytes: The xml output as bytes.
        """
        if path == None:
            if self.filename:
                path = self.filename
        else:
            self.filename = path

        # if path != None:
        #     path = getHDFile(
        #         path,
        #         HD = self.HD,
        #         TabHD = self.TabHD,
        #     )

        if removeImageFiles:
            self.removeImageFiles()

        if path != None:
            if exportImage:
                if self.format == self.Format.PAGES:
                    index = 0
                    for page in self.pages:
                        index += 1

                        filename = os.path.splitext(path)[0]
                        filename = f'{filename}_split_{str(index)}.{format}'

                        page.file = filename
                        page.exportAtlas(filename = filename, format = format)

                else:
                    page = self.pages[0]

                    filename = os.path.splitext(path)[0]
                    filename = f'{filename}.{format}'

                    page.file = filename
                    page.exportAtlas(filename = filename, format = format)

        if self.format == self.Format.IMAGELIST:
            page = self.pages[0]
            xml = page.getXML(format = self.format)
        else:
            xml = etree.Element('Imagelist')
            for page in self.pages:
                xml.append(page.getXML(format = self.format))

        xmloutput = etree.tostring(
            xml, pretty_print = True, xml_declaration = True, encoding = 'utf-8'
        )

        if path != None:
            path = getHDFile(path, HD = self.HD, TabHD = self.TabHD)

            if (file := self.filesystem.get(path)) != None:
                if isinstance(file, Folder):
                    raise TypeError(f'Path {path} is not a file.')

                file.write(xmloutput)

            else:
                file = self.filesystem.add(path, xmloutput)

        output = {'xml': xmloutput, 'images': [a.atlas for a in self.pages]}

        return output

    def combinePages(self):
        """Combine all the pages in this Imagelist into 1 Page
        """
        if self.format == self.Format.IMAGELIST:
            return

        main = self.pages[0]
        for i in range(len(self.pages) - 1):
            page: self.Page = self.pages[i + 1]
            for name in page.images:
                image = page.images[name]
                main.add(image.name, image.image, image.properties, replace = False)

        main.id = None
        main.exportAtlas()

        self.format = self.Format.IMAGELIST

        self.pages = [main]

    def add(
        self,
        name: str,
        image: PIL.Image.Image,
        properties: dict = {},
        page: int | str = 0,
        replace = False
    ):
        """Add image to imagelist.

        Args:
            name (str): Name of image file used in-game.
            image (PIL.Image.Image): Image to use.
            properties (dict, optional): Additional properties for image. Defaults to {}.
            replace (bool, optional): Whether to replace existing image if there is a conflict. Defaults to False.

        Raises:
            NameError: Image already exists.
        
        Returns:
            Imagelist.Page.Image: Resulting imagelist image.
        """
        page: Imagelist.Page = self.getPage(page)

        if page != None:
            return page.add(
                name = name,
                image = image,
                properties = properties,
                replace = replace,
            )

    def get(self, name: str):
        """Get image from imagelist.

        Args:
            name (str): Name of image.

        Returns:
            Imagelist.Page.Image: Imagelist Image.
        """
        for page in self.pages:
            image = page.get(name)
            if image:
                return image

        return None

        # return self.filesystem.get(os.path.join(self.textureBasePath, name))

    def removeImageFiles(self):
        """Remove all image files in imagelist from filesystem.
        """
        for page in self.pages:
            page.removeImageFiles()

    def getPage(self, id: int | str = 0) -> 'Imagelist.Page':
        """Get the page with this id / index.

        Args:
            id (int | str, optional): The id or index of the page. Defaults to 0.

        Raises:
            TypeError: id must be int or str

        Returns:
            Imagelist.Page: The page that has the id or index.
        """
        if isinstance(id, (int, float)):
            id = int(id)
            return self.pages[id]
        elif isinstance(id, str):
            return [p for p in self.pages if p.id == id][0]
        else:
            raise TypeError('id must be int or str')

    class Page(GameObject):

        def __init__(
            self,
            element: etree.ElementBase,
            filesystem: Filesystem | Folder = None,
            gamepath: str = None,
            assets: str = '/assets',
            HD: bool = False,
            TabHD: bool = False,
            save_images: bool = False,
        ) -> None:
            """Page for Imagelist. This is also used when imagelist is not in pages format.

            Args:
                element (etree.Element): lxml elment
                filesystem (Filesystem | Folder, optional): Filesystem to use. Defaults to None.
                gamepath (str, optional): Gamepath used if filesystem is not specified. Defaults to None.
                assets (str, optional): Assets path relative to gamepath. Only used if filesystem is not specified. Defaults to '/assets'.
                HD (bool, optional): Use HD graphics. Defaults to False.
                save_images (bool, optional): Save images in filesystem. Note: this may take more time to load the imagelist. Defaults to False.
            """
            super().__init__(filesystem, gamepath, assets)

            self.HD = HD
            self.TabHD = TabHD

            self.xml: etree.ElementBase = element

            self.atlas = None
            self.images: list[Imagelist.Page.Image] = []
            self.properties: dict[str, str] = {}

            self.read(save_images = save_images)

        def read(self, save_images: bool = False):
            """Read xml.
            
            Args:
                save_images (bool, optional): Save images in filesystem. Note: this may take more time to load the imagelist. Defaults to False.
            """
            self.properties = deepcopy(self.xml.attrib)

            # if self.gamepath:
            #     self.fullAtlasPath = joinPath(self.gamepath, self.assets, self.file)
            # print(self.fullAtlasPath)

            self.getAtlas()
            self.getImages(save_images = save_images)

        @property
        def imgSize(self) -> tuple[int, int]:
            """The size of the image in the properties. Does not have to reflect the size of the atlas.

            Returns:
                tuple[int,int]: (width,height)
            """
            if 'imgSize' in self.properties:
                return tuple([int(v) for v in self.properties['imgSize'].split()])
            else:
                return (1, 1)

        @imgSize.setter
        def imgSize(self, size: tuple | list | str):
            if isinstance(size, (list, tuple)):
                self.properties['imgSize'] = ' '.join([str(a) for a in size])
            elif isinstance(size, str):
                self.properties['imgSize'] = size
            else:
                raise TypeError('size must be a tuple, list, or str')

        @property
        def textureBasePath(self) -> str:
            """The base Textures path, or the place where the files are extracted to.

            Returns:
                str: The textureBasePath
            """
            if 'textureBasePath' in self.properties:
                return self.properties['textureBasePath']
            else:
                self.textureBasePath = joinPath(
                    self.filesystem.baseassets, '/Textures/'
                )
                return self.textureBasePath

        @textureBasePath.setter
        def textureBasePath(self, path):
            self.properties['textureBasePath'] = path

        @property
        def file(self) -> str:
            """The path to the atlas file to use in this ImageList

            Returns:
                str: Path to atlas file.
            """
            if 'file' in self.properties:
                return self.properties['file']
            else:
                return ''

        @file.setter
        def file(self, path):
            self.properties['file'] = path

        @property
        def id(self):
            """Page id

            Returns:
                str: The id
            """
            if 'id' in self.properties:
                return self.properties['id']
            else:
                return None

        @id.setter
        def id(self, value: int, str):
            if isinstance(value, str):
                self.properties['id'] = value
            else:
                self.properties['id'] = str(value)

        def getAtlas(self):
            """Get atlas image.
            """
            if self.file in ['', None]:
                self.atlas = Texture(PIL.Image.new('RGBA', self.imgSize)).image
            else:
                self.atlas = Texture(
                    self.file,
                    HD = self.HD,
                    TabHD = self.TabHD,
                    filesystem = self.filesystem,
                    gamepath = self.gamepath,
                    assets = self.assets,
                    baseassets = self.baseassets,
                ).image

        def getImages(self, save_images = False):
            """Get images from xml.
            Args:
                save_images (bool, optional): Save images in filesystem. Note: this may take more time to load the imagelist. Defaults to False.
            """
            for element in self.xml:
                if element is etree.Comment:
                    continue

                if element.tag == 'Image':
                    image = self.Image(
                        self.atlas,
                        properties = element.attrib,
                        textureBasePath = self.textureBasePath,
                        filesystem = self.filesystem.get(self.textureBasePath),
                        save_image = save_images,
                    )
                    self.images.append(image)

        def get(self, name: str) -> 'Imagelist.Page.Image':
            """Get an image from the imagelist

            Args:
                name (str): Name of image.

            Returns:
                Imagelist.Page.Image: Imagelist Image.
            """
            for image in self.images:
                if image.name == name:
                    return image

        def add(
            self,
            name: str,
            image: PIL.Image.Image,
            properties: dict = None,
            replace = False,
        ) -> 'Imagelist.Page.Image':
            """Add image to imagelist.

            Args:
                name (str): Name of image file used in-game.
                image (PIL.Image.Image): Image to use.
                properties (dict, optional): Additional properties for image. Defaults to {}.
                replace (bool, optional): Whether to replace existing image if there is a conflict. Defaults to False.

            Raises:
                NameError: Image already exists.
            
            Returns:
                Imagelist.Page.Image: Resulting imagelist image.
            """
            existing = self.get(name)
            if existing:
                # print(f'Warning: "{name}" already in imagelist.')
                if not replace:
                    raise NameError(f'Image "{name}" already exists.')

                self.images.remove(existing)

            if properties == None:
                properties = {}

            properties = deepcopy(properties)

            properties['name'] = name
            properties['rect'] = ' '.join([str(_) for _ in (0, 0) + image.size])

            texture = self.Image(
                image,
                properties,
                textureBasePath = self.textureBasePath,
                filesystem = self.filesystem,
                gamepath = self.gamepath,
                assets = self.assets,
                save_image = True,
            )
            self.images.append(texture)

            self._getRects()

            return texture

        def update(self, gap: tuple[int, int] = (1, 1), auto_fit = False):
            """Update the atlas image.

            Args:
                gap (tuple[int,int], optional): The gap between images. Defaults to (1,1).
                auto_fit (bool, optional): Auto minimize the atlas image size while keeping all the sprites in the image. Defaults to False.
            """
            for image in self.images:
                image.image

            self._getRects(gap = gap, auto_fit = auto_fit)
            self._updateAtlas()

            return self.atlas

        def exportAtlas(
            self,
            filename = None,
            gap: tuple = (1, 1),
            auto_fit = False,
            format: str = 'webp',
        ):
            """Export the atlas image into the Filesystem. This function recreates the imagelist, so you need to also export the xml using `getXML()`.

            Args:
                gap (tuple, optional): Gap between each image. Defaults to (1,1).
                filename (str, optional): Filename of image. Defaults to `file` property.
                auto_fit (bool, optional): Auto minimize the atlas image size while keeping all the sprites in the image. Defaults to False.
                format (str, optional): Format to save image as. Defaults to 'webp'.

            Returns:
                PIL.Image.Image: PIL Image.
            """
            self.update(gap = gap, auto_fit = auto_fit)
            file = io.BytesIO()

            self.atlas.save(file, format = format, lossless = True, exact = True)

            if filename == None:
                filename = f'{os.path.splitext(self.file)[0]}.{format}'

            self.file = filename

            filename = getHDFile(filename, self.HD, self.TabHD)

            if self.filesystem.exists(filename):
                self.filesystem.get(filename).rawdata = file
            else:
                self.filesystem.add(filename, file.getvalue())

            return self.atlas

        def getXML(self, filename = None, format: int = 1):
            """Generates the xml for the page / imagelist.

            Args:
                filename (str, optional): Name of image. Defaults to file property.
                format (int, optional): Format of file. 0 for `Imagelist`, 1 for `Page`. Defaults to 1.

            Returns:
                lxml.etree.Element: lxml Element.
            """
            if filename != None:
                self.file = filename

            tag = 'Page' if format else 'ImageList'

            self.imgSize = self.atlas.size

            xml: etree.ElementBase = etree.Element(tag, **self.properties)

            for image in self.images:
                xml.append(image.getXML())

            self.xml = xml
            return self.xml

        def removeImageFiles(self):
            """Remove all image files from filesystem.
            """
            for image in self.images:
                image.removeFile()

        def _getRects(self, gap: tuple = (1, 1), auto_fit = False):
            """Update the rect for all images.

            Args:
                gap (tuple, optional): Gap between images. Defaults to (1,1).
                auto_fit (bool, optional): Auto minimize the atlas image size while keeping all the sprites in the image. Defaults to False.
            """

            x, y = gap
            maxheight = maxwidth = 0
            row = column = 0

            for image in self.images:
                image.rect = (x, y) + image.size

                if x > maxwidth:
                    maxwidth = x

                x += image.size[0] + gap[0]

                column += 1
                if x > self.imgSize[0]:
                    x = gap[0]
                    y += maxheight + gap[1]
                    maxheight = 0
                    column = 0
                    row += 1

                if column == 0:
                    image.rect = (x, y) + image.size
                    x += image.size[0] + gap[0]

                if image.size[1] > maxheight:
                    maxheight = image.size[1]

            y += maxheight + gap[1]

            if auto_fit:
                self.imgSize = (maxwidth, y)
            elif y > self.imgSize[1]:
                self.imgSize = (self.imgSize[0], y)

        def _updateAtlas(self) -> PIL.Image.Image:
            """Update the atlas image.

            Returns:
                PIL.Image.Image: PIL Image.
            """
            atlas: PIL.Image.Image = PIL.Image.new('RGBA', self.imgSize)

            for image in self.images:
                image.atlas = atlas
                atlas.paste(image.image, image.rect[0:2])

            self.atlas = atlas

            # self.atlas = Texture(
            #     atlas,
            #     filesystem = self.filesystem,
            #     gamepath = self.gamepath,
            #     assets = self.assets,
            #     baseassets = self.baseassets,
            #     HD = self.HD,
            #     TabHD = self.TabHD,
            # )
            return self.atlas

        class Image(GameObject):

            def __init__(
                self,
                atlas: PIL.Image.Image,
                properties: dict,
                textureBasePath = '/Textures',
                filesystem: Filesystem | Folder = None,
                gamepath: str = None,
                assets: str = '/assets',
                baseassets: str = '/',
                save_image: bool = False,
            ) -> None:
                """Image for Imagelist

                Args:
                    atlas (PIL.Image.Image): Atlas file containing all images
                    properties (dict): Properties for Image.
                    filesystem (Filesystem | Folder, optional): Filesystem to use. Defaults to None.
                    gamepath (str, optional): Game path. Only used if filesystem not specified. Defaults to None.
                    assets (str, optional): Assets path relative to game path. Only used if filesystem not specified. Defaults to '/assets'.
                    baseassets (str, optional): Base assets path within the assets folder, e.g. `/perry/` in wmp. Defaults to `/`
                    save_image (bool, optional): Save the current image in the filesystem on load. Defaults to False.
                """
                super().__init__(filesystem, gamepath, assets, baseassets)

                self.atlas = atlas
                self.properties = deepcopy(properties)
                self.textureBasePath: str = textureBasePath
                self.rawdata = io.BytesIO()

                self._image = None

                if save_image:
                    self.getImage()

            @property
            def size(self) -> tuple[int, int]:
                """The size of the image.

                Returns:
                    tuple[int,int]: (width,height)
                """
                if 'size' in self.properties:
                    return tuple([int(v) for v in self.properties['size'].split()])
                else:
                    self.size = self.image.size
                    return self.size

            @size.setter
            def size(self, value: tuple | list | str):
                if isinstance(value, (tuple, list)):
                    self.properties['size'] = ' '.join([str(v) for v in value])
                elif isinstance(value, (int, float)):
                    self.properties['size'] = ' '.join([str(int(value))] * 2)
                elif isinstance(value, str):
                    self.properties['size'] = value
                else:
                    raise TypeError('value must be tuple, list or str')

            @property
            def offset(self) -> tuple[int, int]:
                """The image offset

                Returns:
                    tuple[int,int]: (x,y)
                
                (I have no idea what this is for)
                """
                if 'offset' in self.properties:
                    return tuple([int(v) for v in self.properties['offset'].split()])
                else:
                    self.offset = (0, 0)
                    return self.offset

            @offset.setter
            def offset(self, value: tuple | list | str):
                if isinstance(value, (tuple, list)):
                    self.properties['offset'] = ' '.join([str(v) for v in value])
                elif isinstance(value, (int, float)):
                    self.properties['offset'] = ' '.join([str(int(value))] * 2)
                elif isinstance(value, str):
                    self.properties['offset'] = value
                else:
                    raise TypeError('value must be tuple, list or str')

            @property
            def rect(self) -> tuple[int, int, int, int]:
                """The rectangle of this image inside the atlas

                Returns:
                    tuple[int,int,int,int]: (x,y,width,height)
                """

                if 'rect' in self.properties:
                    return tuple([int(v) for v in self.properties['rect'].split()])
                else:
                    self.rect = (0, 0) + self.size
                    return self.rect

            @rect.setter
            def rect(self, value: tuple | list | str):
                if isinstance(value, (tuple, list)):
                    self.properties['rect'] = ' '.join([str(v) for v in value])
                elif isinstance(value, (int, float)):
                    self.properties['rect'] = ' '.join(['0', '0'] +
                                                       ([str(int(value))] * 2))
                elif isinstance(value, str):
                    self.properties['rect'] = value
                else:
                    raise TypeError('value must be tuple, list or str')

            @property
            def name(self) -> str:
                """The name of the image

                Returns:
                    str: image name
                """
                if 'name' in self.properties:
                    return self.properties['name']
                else:
                    self.name = 'image.png'
                    return self.name

            @name.setter
            def name(self, name: str):
                self.properties['name'] = str(name)

            @property
            def image(self):
                """The resulting PIL Image.

                Returns:
                    PIL.Image.Image: PIL Image.
                """
                if self._image == None:
                    self.getImage()

                return self._image.copy()

            @image.setter
            def image(self, image: PIL.Image.Image):
                self._image = image.copy()

            def getImage(self) -> PIL.Image.Image:
                """Get image from atlas.

                Returns:
                    PIL.Image.Image: PIL Image.
                """
                self._image = self.atlas.crop(
                    numpy.add(self.rect, (0, 0) + self.rect[0:2])
                )
                self._image = self._image.resize(self.size)

                self._image.save(
                    self.rawdata, format = os.path.splitext(self.name)[1][1::].upper()
                )
                return self._image

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
                self.image.show(*args, **kwargs)

            def getXML(self, tag = 'Image'):
                """Get xml for image.

                Returns:
                    lxml.etree.Element: lxml element
                """
                xml: etree.ElementBase = etree.Element(tag, **self.properties)

                return xml

            def removeFile(self):
                """Remove file from filesystem.
                """
                return self.filesystem.remove(self.filename)

            def saveFile(self, replace: bool = False):
                """Save image to filesystem.

                Args:
                    replace (bool, optional): Whether to replace any existing file. Defaults to False.
                """
                self.image.save(self.rawdata, os.path.splitext(self.name)[1][1::])
                self.filesystem.add(
                    self.name,
                    content = self.rawdata.getvalue(),
                    replace = replace,
                )

            @property
            def filename(self) -> str:
                """Image filepath in the Filesystem

                Returns:
                    str: Full filepath in the Filesystem
                """
                file = self.filesystem.get(self.name)
                if file != None:
                    return file.path

                return self.name

            def __str__(self) -> str:
                return etree.tostring(self.getXML()).decode()

            def __repr__(self) -> str:
                return etree.tostring(
                    self.getXML(
                        f'{self.__class__.__module__}.{self.__class__.__qualname__}'
                    )
                ).decode()

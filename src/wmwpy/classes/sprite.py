import logging
from lxml import etree
from PIL import Image
import numpy
from copy import deepcopy
import math
import typing
import os

LOADED_ImageTk = True
if LOADED_ImageTk:
    try:
        from PIL import ImageTk
    except:
        LOADED_ImageTk = False

from .imagelist import Imagelist
from ..utils.filesystem import *
from ..utils.gif import save_transparent_gif
from ..utils.XMLTools import strbool
from ..utils import path
from ..gameobject import GameObject
from .texture import Texture


class Sprite(GameObject):
    """wmwpy Sprite.
    
    Attributes:
        HD (bool): Using HD images.
        TabHD (bool): Using TabHD images.
        properties (dict[str,str]): Sprite properties.
        animations (list[Sprite.Animation]): List of animations.
        scale (float): The image scale.
    """

    TEMPLATE = b"""<?xml version="1.0"?>
<Sprite>
</Sprite>
"""

    def __init__(
        self,
        file: str | bytes | File = None,
        filesystem: Filesystem | Folder = None,
        gamepath: str = None,
        assets: str = '/assets',
        baseassets: str = '/',
        properties: dict = {},
        scale: float = 50,
        HD: bool = False,
        TabHD: bool = False,
    ) -> None:
        """Game sprite.

        Args:
            file (str | bytes | File): Sprite file.
            filesystem (Filesystem | Folder, optional): Filesystem to use. Defaults to None.
            gamepath (str, optional): Game path. Only used if filesystem not specified. Defaults to None.
            assets (str, optional): Assets path relative to game path. Only used if filesystem not specified. Defaults to '/assets'.
            baseassets (str, optional): Base assets path within the assets folder, e.g. `/perry/` in wmp. Defaults to `/`
            properties (dict, optional): Sprite properties. Defaults to {}.
            scale (int, optional): Sprite image scale. Defaults to 10.
            HD (bool, optional): Use HD images. Defaults to False.
            TabHD (bool, optional): Use TabHD images. Defaults to False.
        """

        super().__init__(filesystem, gamepath, assets, baseassets)

        self.file = super().get_file(file, template = self.TEMPLATE)

        self.xml: etree.ElementBase = etree.parse(self.file).getroot()

        self.HD = HD
        self.TabHD = TabHD

        self.properties = deepcopy(properties)
        self._properties = deepcopy(self.properties)
        self.animations: list[Sprite.Animation] = []

        self.SAFE_MODE = False

        self.scale = scale

        self.readXML()
        self.animation = 0

    def setAnimation(self, animation: str | int):
        """Set the current animation for the Sprite

        Args:
            animation (str | int): Animation name or index.
        """
        self.animation = animation

    @property
    def SAFE_MODE(self) -> bool:
        """A "safe mode" where you can modify the properties without them being added to the output xml.

        Returns:
            bool: The current state.
        """
        if not hasattr(self, '_SAFE_MODE'):
            self._SAFE_MODE = False

        return self._SAFE_MODE

    @SAFE_MODE.setter
    def SAFE_MODE(self, mode: bool):
        if not isinstance(mode, bool):
            raise TypeError('mode must be True or False')

        if mode:
            if not self.SAFE_MODE:
                self._properties = deepcopy(self.properties)
                self._image = None
        else:
            if self.SAFE_MODE:
                self.properties = deepcopy(self._properties)
                self._image = None

        for animation in self.animations:
            animation.SAFE_MODE = mode

        self._SAFE_MODE = mode

    @property
    def image(self) -> Image.Image:
        """Image of sprite

        Returns:
            PIL.Image.Image: PIL Image
        """
        logging.debug(f'sprite {self.filename}')
        if self.SAFE_MODE:
            if hasattr(self, '_image'):
                if isinstance(self._image, Image.Image):
                    return self._image.copy()

        image = self.animation.image.copy()
        gridSize = numpy.array(self.gridSize)

        # print(f'{gridSize = }')
        # print(f'{self.scale = }')

        size = gridSize * self.scale
        size = [max(1, abs(round(x))) for x in size]
        image = image.resize(size)

        image = image.rotate(self.angle, Image.BILINEAR, expand = True)

        self._image = image
        return image

    @image.setter
    def image(self, image: Image.Image):
        if isinstance(image, Image.Image):
            self._image = image
        else:
            raise TypeError('image must be instance of PIL.Image.Image')

    @property
    def animation(self) -> 'Sprite.Animation':
        """Returns the current animation

        Returns:
            Sprite.Animation: A Sprite.Animation class
        """
        return self._currentAnimation

    @animation.setter
    def animation(self, animation: str | int):
        if isinstance(animation, (int, float)):
            animation = int(animation)
            if animation < len(self.animations):
                self._currentAnimation = self.animations[animation]
        elif isinstance(animation, str):
            for a in self.animations:
                if a.name == animation:
                    self._currentAnimation = a
                    break
        elif isinstance(animation, self.Animation):
            self._currentAnimation = animation

    @property
    def frames(self) -> list['Sprite.Animation.Frame']:
        """Returns the current animation frames.

        Returns:
            list[Sprite.Animation.Frame]: A list of frames.
        """
        return self.animation.frames

    @property
    def frame(self) -> int:
        """The current animation frame.

        Returns:
            int: Current animation frame index.
        """
        return self.animation.frame

    @frame.setter
    def frame(self, value: int):
        self.animation.frame = value

    @property
    def fps(self) -> float:
        return self.animation.fps

    @property
    def filename(self) -> str:
        """Sprite filename
        """
        if 'filename' in self.properties:
            return self.properties['filename']
        else:
            return None

    @filename.setter
    def filename(self, value):
        self.properties['filename'] = value

    def readXML(self):
        """Read Sprite XML
        """
        if self.file == None:
            return

        self.animations = []
        for element in self.xml:
            if element is etree.Comment:
                continue

            if element.tag == 'Animation':
                animation = self.Animation(
                    element,
                    self.filesystem,
                    HD = self.HD,
                    TabHD = self.TabHD,
                )

                self.animations.append(animation)

    def export(self, path: str = None) -> bytes:
        """Export the Sprite XML file

        Args:
            path (str, optional): Path to export into the filesystem. Defaults to the original filename.

        Raises:
            TypeError: Path is not a file.

        Returns:
            bytes: Contents of saved file.
        """
        xml: etree.ElementBase = etree.Element('Sprite')

        for animation in self.animations:
            xml.append(animation.getXML())

        self.xml = xml

        output = etree.tostring(
            xml, pretty_print = True, xml_declaration = True, encoding = 'utf-8'
        )

        if path == None:
            if self.filename:
                path = self.filename

        if path != None:
            if (file := self.filesystem.get(path)) != None:
                if isinstance(file, File):
                    file.write(output)
                else:
                    raise TypeError(f'Path {path} is not a file.')
            else:
                self.filesystem.add(path, output)

        return output

    @property
    def visible(self) -> bool:
        """Whether self Sprite is visible or not
        """
        if 'visible' in self.properties:
            return strbool(self.properties['visible'])
        return False

    @visible.setter
    def visible(self, value: bool | str):
        self.properties['visible'] = str(strbool(value)).lower()

    @property
    def isBackground(self):
        """Whether self Sprite is a background
        """
        if 'isBackground' in self.properties:
            return strbool(self.properties['isBackground'])
        return False

    @isBackground.setter
    def isBackground(self, value: bool | str):
        self.properties['isBackground'] = str(strbool(value)).lower()

    @property
    def gridSize(self) -> tuple[float, float]:
        """The gridSize (size) of self Sprite

        Returns:
            tuple[float,float]: (width,height)
        """
        if 'gridSize' in self.properties:
            return tuple([float(x) for x in self.properties['gridSize'].split()])
        return (1, 1)

    @gridSize.setter
    def gridSize(self, value: tuple[int, int] | str):
        if isinstance(value, str):
            self.properties['gridSize'] = value
        elif isinstance(value, (tuple, list)):
            self.properties['gridSize'] = ' '.join([str(x) for x in value])

    @property
    def pos(self) -> tuple[float, float]:
        """Position of Sprite relative to the center of the Object

        Returns:
            tuple[float,float]: (x,y)
        """
        if 'pos' in self.properties:
            return tuple([float(x) for x in self.properties['pos'].split()])
        return (0, 0)

    @pos.setter
    def pos(self, value: tuple[int, int] | str):
        if isinstance(value, str):
            self.properties['pos'] = value
        elif isinstance(value, (tuple, list)):
            self.properties['pos'] = ' '.join([str(x) for x in value])

    @property
    def angle(self) -> float:
        """Sprite rotation angle

        Returns:
            float: Angle as degrees
        """
        if 'angle' in self.properties:
            return float(self.properties['angle'])
        return 0

    @angle.setter
    def angle(self, value: int | float):
        self.properties['angle'] = str(value)

    def getAnimation(
        self,
        duration: int = 0,
        fps: float = 0,
    ) -> dict[typing.Literal[
        'fps',
        'frame_duration',
        'frames',
    ], float | int | list[Image.Image]]:
        """Get the animation of self object

        Args:
            duration (int, optional): Duration of animation in seconds. If 0, it will try to create a perfect loop. Defaults to 0.
            fps (float, optional): The fps of the animation. If 0, it will try to detect the fps that works for all the sprites. Defaults to 0.

        Raises:
            TypeError: 'fps must be an int or float'
        """
        return self.animation.getAnimation(
            duration = duration,
            fps = fps,
        )

    def saveGIF(
        self,
        filename: str = None,
        duration: int = 0,
        fps: float = 0,
    ):
        """Save current animation as a gif.

        Args:
            filename (str, optional): The filename to save this animation gif as. Defaults to None.
            duration (int, optional): The duration of the gif in seconds. If it's 0, it automatically finds a perfect loop. Defaults to 0.
            fps (float, optional): The frames per second of the animation. If it's 0, it is automatically calculated. Defaults to 0.

        Returns:
            PIL.Image.Image: The resulting PIL Image object.
        """
        if filename in ['', None]:
            filename = f'{os.path.splitext(os.path.basename(self.filename))[0]}-{self.animation.name}.gif'

        self.animation.saveGIF(
            filename = filename,
            duration = duration,
            fps = fps,
        )

    class Animation(GameObject):
        """Animation object for wmwpy Sprite.
        
        Attributes:
            HD (bool): Using HD images.
            TabHD (bool): Using TabHD images.
            properties (dict[str,str]): The animation properties.
            frames (list[Sprite.Animation.Frame]): List of frames.
            frame (int): The current animation frame.
        
        """
        TEMPLATE = """<Animation>
</Animation>
"""

        def __init__(
            self,
            xml: str | etree.ElementBase = None,
            filesystem: Filesystem | Folder = None,
            gamepath: str = None,
            assets: str = '/assets',
            baseassets: str = '/',
            HD: bool = False,
            TabHD: bool = False,
        ) -> None:
            """Animation for Sprite.

            Args:
                xml (str | etree.Element): lxml.etree Element xml element for sprite.
                filesystem (Filesystem | Folder, optional): Filesystem to use. Defaults to None.
                gamepath (str, optional): Game path. Only used if filesystem not specified. Defaults to None.
                assets (str, optional): Assets path relative to game path. Only used if filesystem not specified. Defaults to '/assets'.
                baseassets (str, optional): Base assets path within the assets folder, e.g. `/perry/` in wmp. Defaults to `/`
                HD (bool, optional): Use HD images. Defaults to False.
                TabHD (bool, optional): Use TabHD images. Defaults to False.
            """
            super().__init__(filesystem, gamepath, assets, baseassets)

            if isinstance(xml, str):
                self.xml: etree.ElementBase = etree.XML(xml).getroot()
            elif isinstance(xml, etree._Element):
                self.xml = xml
            elif xml == None:
                self.xml = etree.XML(self.TEMPLATE)

            self.HD = HD
            self.TabHD = TabHD

            self.properties = {}

            self._PhotoImage = None

            self.frames: list[Sprite.Animation.Frame] = []
            self.frame = 0

            self.readXML()

            self.SAFE_MODE = False

        @property
        def SAFE_MODE(self) -> bool:
            """A "safe mode" where you can modify the properties without them being added to the output xml.

            Returns:
                bool: The current state.
            """
            if not hasattr(self, '_SAFE_MODE'):
                self._SAFE_MODE = False

            return self._SAFE_MODE

        @SAFE_MODE.setter
        def SAFE_MODE(self, mode: bool):
            if not isinstance(mode, bool):
                raise TypeError('mode must be True or False')

            if mode:
                if not self.SAFE_MODE:
                    self._properties = deepcopy(self.properties)
            else:
                if self.SAFE_MODE:
                    self.properties = deepcopy(self._properties)

            for frame in self.frames:
                frame.SAFE_MODE = mode

            self._SAFE_MODE = mode

        @property
        def image(self) -> Image.Image:
            """Current Animation image

            Returns:
                PIL.Image.Image: PIL Image
            """

            return self.frames[self.frame].image

        @property
        def frame(self) -> int:
            """Current animation frame.

            Returns:
                int: Current animation frame index.
            """
            return self._frame

        @frame.setter
        def frame(self, value: int):
            if len(self.frames) > 0:
                self._frame = int(value) % len(self.frames)
            else:
                self._frame = 0

        @property
        def PhotoImage(self) -> 'ImageTk.PhotoImage':
            """Tkinter PhotoImage for the Animation
            """
            if LOADED_ImageTk:
                self._PhotoImage = ImageTk.PhotoImage(self.image)
            else:
                self._PhotoImage = self.image.copy()

            return self._PhotoImage

        def readXML(self):
            """Read the xml for self Animation
            """
            self.getAttributes()
            self.getFrames()

        def getAttributes(self):
            """Get all the attributes of self Animation
            """
            self.properties = self.xml.attrib

        @property
        def name(self) -> str:
            """Name of self animation.

            Returns:
                str: The name of self animation.
            """
            if 'name' in self.properties:
                return self.properties['name']
            else:
                return ''

        @name.setter
        def name(self, value: str):
            if not isinstance(value, str):
                raise TypeError('name must be str')

            self.properties['name'] = value

        @property
        def textureBasePath(self) -> str:
            """The textureBasePath where all textures are stored.

            Returns:
                str: textureBasePath.
            """
            if 'textureBasePath' in self.properties:
                return self.properties['textureBasePath']
            else:
                if self.filesystem == None:
                    return '/Textures/'

                self.textureBasePath = path.joinPath(
                    self.filesystem.baseassets, '/Textures/'
                )
                return self.textureBasePath

        @textureBasePath.setter
        def textureBasePath(self, path):
            if isinstance(path, Folder):
                path = path.path
            if not isinstance(path, str):
                raise TypeError('path must be str')

            self.properties['textureBasePath'] = path

        @property
        def atlasPath(self) -> str:
            """The path to the atlas.

            Returns:
                str: The path to the atlas file.
            """
            if 'atlas' in self.properties:
                return self.properties['atlas']
            else:
                return None

        @atlasPath.setter
        def atlasPath(self, path):
            self.atlas = path

        @property
        def atlas(self) -> Imagelist:
            if hasattr(self, '_atlas') and isinstance(self._atlas, Imagelist):
                self.properties['atlas'] = self._atlas.filename
                return self._atlas

            if 'atlas' in self.properties:
                self._atlas = Imagelist(
                    self.filesystem.get(self.properties['atlas']),
                    self.filesystem,
                    HD = self.HD,
                    TabHD = self.TabHD,
                )
            else:
                self._atlas = None

            return self._atlas

        @atlas.setter
        def atlas(self, path):
            if isinstance(path, str):
                self._atlas = Imagelist(
                    self.filesystem.get(self.properties['atlas']),
                    self.filesystem,
                    HD = self.HD,
                    TabHD = self.TabHD,
                )
            elif isinstance(path, Imagelist):
                self._atlas = path
            else:
                raise TypeError('atlas must be str or Imagelist')

        @property
        def texture(self) -> Texture:
            """The texture for this animation. Sometimes used instead of an atlas.

            Returns:
                Texture: The Texture.
            """
            if hasattr(self, '_texture') and isinstance(self._texture, Texture):
                self.properties['texture'] = self._texture.filename
                return self._texture

            if 'texture' in self.properties:
                self._texture = Texture(
                    self.properties['texture'],
                    filesystem = self.filesystem,
                    gamepath = self.gamepath,
                    assets = self.assets,
                    baseassets = self.baseassets,
                    HD = self.HD,
                    TabHD = self.TabHD,
                )

            else:
                self._texture = None

            return self._texture

        @texture.setter
        def texture(self, path):
            if isinstance(path, str):
                self.properties['texture'] = path
            elif isinstance(path, File):
                self.properties['texture'] = path.path
            elif isinstance(path, Texture):
                self.properties['texture'] = path.filename
                self._texture = path
            else:
                raise TypeError('texture must be a path, File, or Texture object')

        @property
        def playbackMode(self) -> str:
            """The playback mode.

            Returns:
                str: The current playback mode.
            """
            if 'playbackMode' in self.properties:
                return self.properties['playbackMode']
            else:
                return 'ONCE'

        @playbackMode.setter
        def playbackMode(self, mode):
            if not isinstance(mode, str):
                raise TypeError('playbackMode must be str')

        @property
        def loopCount(self) -> int:
            """The loopCount for this Animation.
            
            Returns:
                int: The loopCount.
            """
            if 'loopCount' in self.properties:
                return int(self.properties['loopCount'])
            else:
                return 0

        @loopCount.setter
        def loopCount(self, count):
            if not isinstance(count, (str, int, float)):
                raise TypeError('loopCount must be str or int')

            self.properties['loopCount'] = str(count)

        def getFrames(self) -> list['Sprite.Animation.Frame']:
            """Get a list of all the Animation `Frame`s

            Returns:
                list[Sprite.Animation.Frame]: List of all the Frames in this Animation.
            """
            self.frames = []

            if self.xml == None:
                return None
            for f in self.xml:
                if (not f is etree.Comment) and f.tag == 'Frame':
                    self.frames.append(
                        self.Frame(
                            f.attrib,
                            self.atlas if self.atlas != None else self.texture,
                            self.textureBasePath,
                            filesystem = self.filesystem,
                            gamepath = self.gamepath,
                            assets = self.assets,
                            baseassets = self.baseassets,
                        )
                    )

            return self.frames

        def updateProperties(self):
            """Update the Sprite properties
            """

            def updateProperty(property: str, value, default = None):
                if default != None and value == default:
                    if property in self.properties:
                        del self.properties[property]
                else:
                    self.properties[property] = value

            updateProperty('name', self.name)
            updateProperty('textureBasePath', self.textureBasePath)
            self.atlas.export(self.atlasPath, exportImage = True)
            updateProperty('atlas', self.atlasPath)
            updateProperty('fps', str(self.fps))
            updateProperty('playbackMode', self.playbackMode)
            updateProperty('loopCount', str(self.loopCount))

        def getXML(self):
            """Get the XML of this Animation

            Returns:
                etree.Element: etree Element
            """
            self.updateProperties()
            xml: etree.ElementBase = etree.Element('Animation', **self.properties)

            for frame in self.frames:
                xml.append(frame.getXML())

            self.xml = xml
            return self.xml

        @property
        def fps(self) -> float:
            """The Animation fps.

            Returns:
                float: The Animation fps.
            """
            if 'fps' in self.properties:
                return float(self.properties['fps'])
            else:
                self.fps = 30
                return self.fps

        @fps.setter
        def fps(self, value: int | float | str):
            self.properties['fps'] = str(value)

        def getAnimation(
            self,
            duration: int = 0,
            fps: float = 0,
        ) -> dict[typing.Literal[
            'fps',
            'frame_duration',
            'frames',
        ], float | int | list[Image.Image]]:
            """Get the animation of this object

            Args:
                duration (int, optional): Duration of animation in seconds. If 0, it will try to create a perfect loop. Defaults to 0.
                fps (float, optional): The fps of the animation. If 0, it will try to detect the fps that works for all the sprites. Defaults to 0.

            Raises:
                TypeError: 'fps must be an int or float'
            """
            if not isinstance(fps, (int, float)) and not fps == None:
                raise TypeError('fps must be an int or float')

            if not isinstance(duration, (int, float)) and not duration == None:
                raise TypeError('duration must be an int or float')

            if (fps in [0, None]) or (fps <= 0):
                fps = self.fps

            frames: list[Image.Image] = []
            self.frame = 0
            frame = 0
            time = 0

            def check():
                if duration > 0:
                    return time <= duration

                if (time <= 0) or (frame <= 1):
                    return True
                if self.frame == 0:
                    return False

                return True

                # print(f'test = {( not ((time > 0) and (duration <= 0) and ((sum([sprite.frame for sprite in self.sprites]) == 0))))}')
                # print(f'time check = {((time <= duration) and (duration > 0))}')

            while check():
                self.frame += (frame) % ((fps / self.fps) + 1)

                frames.append(self.image)

                frame += 1
                time += (1000 / fps) / 1000

            # frames = frames[:-1]

            return {
                'fps': fps,
                'frame_duration': (1000 / fps) / 1000,
                'frames': frames,
            }

        def saveGIF(
            self,
            filename = None,
            duration: int = 0,
            fps: float = 0,
        ) -> Image.Image:
            """Save animation as a gif.

            Args:
                filename (str, optional): The filename to save this animation gif as. Defaults to None.
                duration (int, optional): The duration of the gif in seconds. If it's 0, it automatically finds a perfect loop. Defaults to 0.
                fps (float, optional): The frames per second of the animation. If it's 0, it is automatically calculated. Defaults to 0.

            Returns:
                PIL.Image.Image: The resulting PIL Image object.
            """
            if filename == None:
                filename = self.name
                filename = os.path.splitext(filename)[0] + '.gif'

            animation = self.getAnimation(
                duration = duration,
                fps = fps,
            )

            return save_transparent_gif(
                animation['frames'],
                durations = animation['frame_duration'],
                save_file = filename,
            )

        # Frame
        class Frame(GameObject):
            """The Frame for Animations.

            Attributes:
                atlas (Imagelist): The atlas for this Frame.
                textureBasePath (str): The textureBasePath for this Frame.
                properties (dict[str,str]): The frame properties.
            """

            def __init__(
                self,
                properties: dict = {},
                atlas: Imagelist = None,
                textureBasePath: str = None,
                filesystem: Filesystem | Folder = None,
                gamepath: str = None,
                assets: str = '/assets',
                baseassets: str = '/',
            ) -> None:
                """Frame for Sprite.Animation.

                Args:
                    properties (dict): Image properties.
                    atlas (Imagelist, optional): Image atlas for Image. Defaults to None.
                    textureBasePath (str, optional): Directory to put image in. Defaults to None.
                    filesystem (Filesystem | Folder, optional): Filesystem to use. Defaults to None.
                    gamepath (str, optional): Game path. Only used if filesystem not specified. Defaults to None.
                    assets (str, optional): Assets path relative to game path. Only used if filesystem not specified. Defaults to '/assets'.
                    baseassets (str, optional): Base assets path within the assets folder, e.g. `/perry/` in wmp. Defaults to `
                """
                super().__init__(filesystem, gamepath, assets, baseassets)

                self.atlas = atlas
                self.textureBasePath = textureBasePath
                self.properties = properties

                self.color_filter: tuple[int, int, int, int] = []

                self.getImage()

                self.SAFE_MODE = False

            @property
            def SAFE_MODE(self) -> bool:
                """A "safe mode" where you can modify the properties without them being added to the output xml.

                Returns:
                    bool: The current state.
                """
                if not hasattr(self, '_SAFE_MODE'):
                    self._SAFE_MODE = False

                return self._SAFE_MODE

            @SAFE_MODE.setter
            def SAFE_MODE(self, mode: bool):
                if not isinstance(mode, bool):
                    raise TypeError('mode must be True or False')

                if mode:
                    if not self.SAFE_MODE:
                        self._properties = deepcopy(self.properties)
                        self._color_filters = deepcopy(self.color_filter)
                else:
                    if self.SAFE_MODE:
                        self.properties = deepcopy(self._properties)
                        self.color_filter = deepcopy(self._color_filters)

                self._SAFE_MODE = mode

            @property
            def name(self) -> str:
                """The name of this frame.

                Returns:
                    str: The name of this frame.
                """
                if 'name' in self.properties:
                    return self.properties['name']
                else:
                    return ''

            @name.setter
            def name(self, name: str):
                self.properties['name'] = str(name)

            @property
            def offset(self) -> tuple[float, float]:
                """The frame offset.

                Returns:
                    tuple[float,float]: (x,y)
                """
                if 'offset' in self.properties:
                    return tuple([float(x) for x in self.properties['offset'].split()])
                else:
                    return (0, 0)

            @offset.setter
            def offset(self, offset: tuple[float, float]):
                if isinstance(offset, (tuple, list)):
                    self.properties['offset'] = ' '.join([str(x) for x in offset])
                elif isinstance(offset, (int, float)):
                    self.properties['offset'] = ' '.join([str(offset), str(offset)])
                elif isinstance(offset, str):
                    self.properties['offset'] = offset
                else:
                    raise TypeError('offset must be tuple, float or str')

            @property
            def scale(self) -> tuple[float, float]:
                """The frame scale.

                Returns:
                    tuple[float, float]: (x,y)
                """
                if 'scale' in self.properties:
                    return tuple([float(x) for x in self.properties['scale'].split()])
                else:
                    return (1, 1)

            @scale.setter
            def scale(self, scale: tuple[float, float]):
                if isinstance(scale, (tuple, list)):
                    self.properties['scale'] = ' '.join([str(x) for x in scale])
                elif isinstance(scale, (int, float)):
                    self.properties['scale'] = ' '.join([str(scale), str(scale)])
                elif isinstance(scale, str):
                    self.properties['scale'] = scale
                else:
                    raise TypeError('scale must be tuple, float or str')

            @property
            def angleDeg(self) -> float:
                """The frame rotation angle.

                Returns:
                    float: Angle in degrees.
                """
                if 'angleDeg' in self.properties:
                    return float(self.properties['angleDeg'])
                else:
                    return 0

            @angleDeg.setter
            def angleDeg(self, angle: float):
                if isinstance(angle, (int, float, str)):
                    self.properties['angleDeg'] = str(angle)
                else:
                    raise TypeError('angle must be float')

            @property
            def repeat(self) -> int:
                """The amount of times to repeat this frame in the animation.

                Returns:
                    int: The amount of times to repeat.
                """
                if 'repeat' in self.properties:
                    self.repeat = int(self.properties['repeat'])
                else:
                    return 0

            @repeat.setter
            def repeat(self, num: int):
                if isinstance(num, (int, float, str)):
                    self.properties['angleDeg'] = str(int(float(num)))
                else:
                    raise TypeError('angle must be int')

            def getImage(self):
                """Get the image. The image is stored in Frame._image.
                """
                if isinstance(self.atlas, Imagelist):
                    self._image = self.atlas.get(self.name)
                elif self.texture != None:
                    self._image = self.texture

            @property
            def texture(self) -> Texture:
                """The frame Texture instead of atlas.

                Returns:
                    Texture: The Texture object.
                """
                if isinstance(self.atlas, Texture):
                    return self.atlas
                else:
                    return None

            @property
            def image(self) -> Image.Image:
                """Image of this Image

                Returns:
                    PIL.Image.Image: PIL Image
                """
                self.getImage()

                if hasattr(self._image, 'image'):
                    image = self._image.image.copy()
                elif isinstance(self._image, Image.Image):
                    image = self._image.copy()
                else:
                    image = Image.new('RGBA', (1, 1), (0, 0, 0, 0))

                # Validate scale before resize to prevent negative dimensions
                scale_array = numpy.array(self.scale)
                if scale_array[0] <= 0 or scale_array[1] <= 0:
                    # Use original image if scale has negative/zero values
                    image = self._image.image.copy(
                    ) if hasattr(self._image, 'image') else self._image.copy()
                else:
                    image = image.resize(
                        tuple([
                            round(_) for _ in (numpy.array(image.size) * scale_array)
                        ])
                    )
                image = image.rotate(self.angleDeg, expand = True)

                # for color in self.color_filters:
                # if len(self.color_filter) >= 3:
                #     try:
                #         image = imageprocessing.recolor_image(
                #             image,
                #             self.color_filter
                #         )
                #     except:
                #         pass
                # image.show()

                return image

            @image.setter
            def image(self, image: str):
                if isinstance(image, Texture):
                    self.atlas = image
                elif isinstance(self.atlas, Texture):
                    if isinstance(image, str):
                        self.atlas = Texture(
                            image = image,
                            filesystem = self.filesystem,
                            gamepath = self.gamepath,
                            assets = self.assets,
                            baseassets = self.baseassets,
                            HD = self.atlas.HD,
                            TabHD = self.atlas.TabHD,
                        )
                elif isinstance(self.atlas, Imagelist):
                    if isinstance(image, str):
                        self.name = image

                self.getImage()

            def updateProperties(self):
                """Update Image properties
                """

                def updateProperty(property: str, value, default):
                    if value == default:
                        if property in self.properties:
                            del self.properties[property]
                    else:
                        self.properties[property] = value

                self.properties['name'] = self.name

                updateProperty(
                    'offset', ' '.join([str(_) for _ in self.offset]),
                    ' '.join([str(_) for _ in self._offset])
                )

                updateProperty(
                    'scale', ' '.join([str(_) for _ in self.scale]),
                    ' '.join([str(_) for _ in self._scale])
                )

                updateProperty('angleDeg', str(self.angleDeg), str(self._angleDeg))

                updateProperty('repeat', str(self.repeat), str(self._repeat))

            def getXML(self) -> etree.ElementBase:
                """Get the XML for the Frame

                Returns:
                    etree.Element: XML of this Frame
                """
                self.updateProperties()
                return etree.Element('Frame', **self.properties)

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

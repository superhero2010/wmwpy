# main widget class
from ...utils.filesystem import Filesystem, Folder
from ...gameobject import GameObject

from PIL import Image
from lxml import etree

WIDGETS: dict[str, 'Widget'] = {}


class Widget(GameObject):

    def __init__(
        self,
        xml: etree.ElementBase = None,
        filesystem: Filesystem | Folder = None,
        gamepath: str = None,
        assets: str = '/assets',
        baseassets: str = '/',
        screenSize: tuple = (900, 720),
    ) -> None:
        """
            Main widget
        """
        if xml == None:
            return

        super().__init__(filesystem, gamepath, assets, baseassets)

        self.xml = xml
        self.properties = self.xml.attrib
        self.type = self.properties['type']

        self.pos = (0, 0)
        self.size = (0, 0)
        self.id = 0
        self.layer = 0

        self.forceAspect = False
        self.visible = True

        self.getValues()

        self.image = Image.new('RGBA', (100, 100))

    def getValues(self):
        if 'pos' in self.properties:
            self.pos = [float(v) for v in tuple(self.properties['pos'].split(' '))]

        if 'id' in self.properties:
            self.id = float(self.properties['id'])

        if 'layer' in self.properties:
            self.layer = float(self.properties['layer'])

        if 'size' in self.properties:
            self.size = [float(v) for v in tuple(self.properties['size'].split(' '))]

        if 'forceAspect' in self.properties:
            self.setForceAspect(self.properties['forceAspect'])

        if 'visible' in self.properties:
            self.visible = bool(self.properties['visible'])

    def setForceAspect(self, aspect = (1, 1)):
        if isinstance(aspect, str):
            forceAspect = tuple([float(v) for v in aspect.split(':')])
        elif not aspect:
            forceAspect = False
        else:
            forceAspect = tuple(aspect)

        self.forceAspect = forceAspect

    @property
    def type(self):
        return self.properties['type']

    @type.setter
    def type(self, value):
        self.properties['type'] = value

        if self.properties['type'] in WIDGETS:
            self.__class__ = WIDGETS[self.properties['type']]
        else:
            self.__class__ = Widget


def register_widget(name: str, class_: Widget):

    if not isinstance(class_, type):
        class_ = class_.__class__

    if not isinstance(class_(None), Widget):
        raise TypeError('class has to be inherited by Widget')
    if not isinstance(name, str):
        raise TypeError('name must be a string')
    try:
        if WIDGETS[name]:
            raise NameError(f'widget "{name}" already exists')
    except:
        pass
    WIDGETS[name] = class_


def get_widget(name, *args, **kwargs) -> Widget:
    if name in WIDGETS:
        return WIDGETS[name](**args, **kwargs)
    else:
        return Widget(**args, **kwargs)

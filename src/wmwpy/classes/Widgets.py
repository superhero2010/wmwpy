import lxml
from lxml import etree
from PIL import Image
from ..utils.waltex import WaltexImage
from .widget import Widget


class Widgets():

    def __init__(
        self,
        element: etree.Element,
        gamePath: str,
        screenSize = (),
        texturePath: str = None,
        baseLayoutFile: str = None
    ) -> None:
        self.element = element

        self.attributes = self.element.attrib

        if not texturePath:
            texturePath = self.attributes['texturePath']
        self.texturePath = texturePath

        if not baseLayoutFile:
            baseLayoutFile = self.attributes['baseLayoutFile']
        self.baseLayoutFile = baseLayoutFile

        self.gamePath = gamePath

        self.widgets = []
        self.comments = []

        self.getWidgets()

    def getWidgets(self):
        for w in self.element:
            if not isinstance(w, etree.Comment):
                widget = Widget(w, self.texturePath)
                self.widgets.append(widget)
            else:
                self.comments.append(w)

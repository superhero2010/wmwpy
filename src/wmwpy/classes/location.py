from lxml import etree

from ..gameobject import GameObject
from ..utils.filesystem import *


class Location(GameObject):
    """Location object for location xml files in WMW2.
    
    Attributes:
        backgrounds (list[dict[str,str]]): List of backgrounds.
        levels (list[dict[str,str]]): List of levels.
        widgets (list[dict[str,str]]): List of widgets.
        sprites (list[dict[str,str]]): List of sprites (if any).
        armatures (list[dict[str,str]]): List of Armatures.
        waterPaths (list[dict[str,str]]): List of WaterPaths.
        atlases (list[dict[str,str]]): List of Atlases.
        expertAtlases (list[dict[str,str]]): List of ExpertAtlases.
        transitionPiece (list[dict[str,str]]): List of TransitionPieces.
        expertModeAssets (list[dict[str,str]]): List of ExpertModeAssets.
        audios (list[dict[str,str]]): List of Audios.
    """

    def __init__(
        self,
        file: File | str | bytes,
        filesystem: Filesystem | Folder = None,
        gamepath: str = None,
        assets: str = '/assets',
        baseassets: str = '/',
    ) -> None:
        """Location in WMW2.

        Args:
            file (File | str | bytes): XML file for the Location.
            filesystem (Filesystem | Folder, optional): Filesystem to use. Defaults to None.
            gamepath (str, optional): Game path. Only used if filesystem not specified. Defaults to None.
            assets (str, optional): Assets path relative to game path. Only used if filesystem not specified. Defaults to '/assets'.
            baseassets (str, optional): Base assets path within the assets folder, e.g. `/perry/` in wmp. Defaults to `/`.
        """
        super().__init__(filesystem, gamepath, assets, baseassets)

        self.file = super().get_file(file)

        self.xml: etree._Element = etree.parse(self.file).getroot()

        self.backgrounds: list[dict[str, str]] = []
        self.levels: list[dict[str, str]] = []
        self.widgets: list[dict[str, str]] = []
        self.sprites: list[dict[str, str]] = []
        self.armatures: list[dict[str, str]] = []
        self.waterPaths: list[dict[str, str]] = []
        self.atlases: list[dict[str, str]] = []
        self.expertAtlases: list[dict[str, str]] = []
        self.transitionPiece: list[dict[str, str]] = []
        self.expertModeAssets: list[dict[str, str]] = []
        self.audios: list[dict[str, str]] = []

        self.read()

    def read(self):
        """Read the XML file.
        """
        if self.xml == None:
            return

        self.backgrounds = []
        self.levels = []
        self.widgets = []
        self.sprites = []
        self.armatures = []
        self.waterPaths = []
        self.atlases = []
        self.expertAtlases = []
        self.transitionPiece = []
        self.expertModeAssets = []
        self.audios = []

        tags = {
            'Backgrounds': self._getBackgrounds,
            'Levels': self._getLevels,
            'Widgets': self._getWidgets,
            'Armatures': self._getArmatures,
            'WaterPaths': self._getWaterPaths,
            'Atlases': lambda xml, atlases = self.atlases: self.
            _getAtlasses(xml, atlases),
            'ExpertAtlases': lambda xml, atlases = self.expertAtlases: self.
            _getAtlasses(xml, atlases),
            'TransitionPiece': self._getTransitionPieces,
            'ExpertModeAssets': self._getExpertModeAssets,
            'Audios': self._getAudios,
        }

        for element in self.xml:
            element: etree._Element
            if element is etree.Comment:
                continue

            if element.tag in tags:
                tags[element.tag](element)

    def _getBackgrounds(self, backgrounds: etree._Element):
        for element in backgrounds:
            element: etree._Element

            if element is etree.Comment:
                continue

            if element.tag == 'Background':
                background = {}

                for property in element:
                    property: etree._Element

                    if property is etree.Comment:
                        continue

                    background[property.tag] = property.get('value')

                self.backgrounds.append(background)

    def _getLevels(self, levels: etree._Element):
        for element in levels:
            element: etree._Element

            if element is etree.Comment:
                continue

            if element.tag == 'Level':
                level = {}

                for property in element:
                    property: etree._Element

                    if property is etree.Comment:
                        continue

                    level[property.tag] = property.get('value')

                self.levels.append(level)

    def _getWidgets(self, widgets: etree._Element):
        for element in widgets:
            element: etree._Element

            if element is etree.Comment:
                continue

            if element.tag == 'Widget':
                widget = {}

                for property in element:
                    property: etree._Element

                    if property is etree.Comment:
                        continue

                    widget[property.tag] = property.get('value')

                self.widgets.append(widget)

    def _getArmatures(self, armatures: etree._Element):
        for element in armatures:
            element: etree._Element

            if element is etree.Comment:
                continue

            if element.tag == 'Armature':
                armature = {}

                for property in element:
                    property: etree._Element

                    if property is etree.Comment:
                        continue

                    armature[property.tag] = property.get('value')

                self.armatures.append(armature)

    def _getWaterPaths(self, waterPaths: etree._Element):
        for element in waterPaths:
            element: etree._Element

            if element is etree.Comment:
                continue

            if element.tag == 'WaterPath':
                waterPath = {}

                for el in element:
                    el: etree._Element

                    if el is etree.Comment:
                        continue

                    if el.tag == 'Name':
                        waterPath['name'] = el.get('value')
                    elif el.tag == 'Properties':
                        properties = {}

                        for property in el:
                            property: etree._Element

                            if property is etree.Comment:
                                continue

                            if property.tag == 'Property':
                                properties[property.get('name')] = property.get('value')

                        waterPath['properties'] = properties

                self.waterPaths.append(waterPath)

    def _getAtlasses(self, xml: etree._Element, atlases: list = None):
        if atlases == None:
            atlases = self.atlases

        for element in xml:
            element: etree._Element

            if element is etree.Comment:
                continue

            if element.tag == 'Atlas':
                atlas = ''

                for FileName in element:
                    FileName: etree._Element

                    if FileName is etree.Comment:
                        continue

                    atlas = FileName.get('value')

                atlases.append(atlas)

    def _getTransitionPieces(self, transitionPieces: etree._Element):
        for element in transitionPieces:
            element: etree._Element

            if element is etree.Comment:
                continue

            if element.tag == 'TransitionPiece':
                level = {}

                for property in element:
                    property: etree._Element

                    if property is etree.Comment:
                        continue

                    level[property.tag] = property.get('value')

                self.levels.append(level)

    def _getExpertModeAssets(self, expertModeAssets: etree._Element):
        for element in expertModeAssets:
            element: etree._Element

            if element is etree.Comment:
                continue

            if element.tag == 'Asset':
                self.expertModeAssets.append(element.get('value'))

    def _getAudios(self, audios: etree._Element):
        for element in audios:
            element: etree._Element

            if element is etree.Comment:
                continue

            if element.tag == 'Audio':
                level = {}

                for property in element:
                    property: etree._Element

                    if property is etree.Comment:
                        continue

                    level[property.tag] = property.get('value')

                self.levels.append(level)

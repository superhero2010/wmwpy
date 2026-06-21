from lxml import etree
import io

# c++ code that can read curves collection files
# =================================================
# https://github.com/DannyTking/TalkingScene/blob/master/TalkingScene/WalaberEngine/Walaber/src/Math/CurveManager.cpp#L406
# https://github.com/DannyTking/TalkingScene/blob/master/TalkingScene/WalaberEngine/Walaber/include/Math/Curve.h#L19
# =================================================
# If anyone know how to read c++ code, please help.


class curvesCollection():
    MAGIC = 0xC081EC54
    MAGIC_V1 = 0xC081EC55

    def __init__(self, file: bytes) -> None:
        if isinstance(file, io.BytesIO):
            file = file.getvalue()
        elif not isinstance(file, bytes):
            raise TypeError('file must be bytes or BytesIO object.')

        self.rawdata = file

        int.from_bytes()

    def read(self):
        self.header = {
            'magic': None,
            'version': None,
            'curves': None,
            'flags': None,
            'groups': None,
        }

        magic = int.from_bytes(self.rawdata[0:4], byteorder = 'little')

        if magic == self.MAGIC:
            self.header['version'] = 1
        elif magic == self.MAGIC_V1:
            self.header['version'] = int(self.rawdata[5])
        else:
            raise ValueError('file not a curves collection .bin file')


if __name__ == "__main__":
    pass

import sys, io, os
from typing import Union

class File(object):
    """Represents a File to be send over a network."""

    def __repr__(self) -> str:
        return f'<file={self.__file__}, mode="{self.__mode__}"'

    def __init__(self, file, mode, *args, **kwargs):
        self.__file__ = open(file, mode, *args, **kwargs)
        self.__filesize__ = self.__file__.read().__sizeof__()
        super().__init__()

    def file(self) -> io.BufferedReader:
        return self.__file__
    
    def mode(self) -> str:
        return self.__file__.mode

    def data(self) -> Union[bytes, str]:
        return self.__file__.read()

class Message(str):
    """Represents a Message to be send over a network."""

    def __repr__(self) -> str:
        return self

    def __str__(self) -> str:
        return f'Message(str={super().__str__()}, file="{self.file}")'

    def __new__(cls, *args, **kwargs):
        cls.file: File = kwargs['file']
        del kwargs['file']

        print(cls.file)

        return str.__new__(cls, *args, **kwargs)

    def size(self) -> int:
        return sys.getsizeof(self)
    
    def in_bytes(self) -> bytes:
        return self.encode()

if __name__ == '__main__':
    file_obj = File(file='demo_file.py', mode='rb')
    print(file_obj.file())
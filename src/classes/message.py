import sys, io, os
from typing import Union

class File(object):
    """Represents a File to be send over a network."""

    def __repr__(self) -> str:
        return f'<file={self.__file__}, mode="{self.__mode__}"'
    
    def __init__(self, file, mode, *args, **kwargs) -> None:
        self.file = file
        self.mode = mode

        super().__init__()

    def file(self) -> Union[io.BufferedReader, io.TextIOWrapper]:
        """Returns the file object for the file provided."""
        return self.file
    
    def mode(self) -> str:
        """Returns the file object mode."""
        return self.file.mode

    def data(self) -> Union[bytes, str]:
        """Returns the file object data."""
        return self.file.read()

class Message(object):
    """Represents a Message to be send over a network."""

    def __repr__(self) -> str:
        return self

    def __str__(self) -> str:
        return f'Message(message="{self.message}", file={self.file})'

    def __init__(self, message: str=None, file: File=None):
        self.message = message
        self.file = file

        super().__init__()

if __name__ == '__main__':
    file_obj = File(file='demo_file.py', mode='rb')
    print(file_obj.file())

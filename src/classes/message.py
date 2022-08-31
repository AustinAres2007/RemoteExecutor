import io
from typing import Union
from inspect import signature

class IPAddress(object):
    pass

class File(object):
    """Represents a File to be send over a network."""

    def __repr__(self) -> str:
        __repr__string = f"{self.__class__.__name__}("
        [__repr__string + f"{meth}: {getattr(self, meth)}, " for meth in signature(self) if meth != 'self']
        __repr__string = __repr__string[:-2] + ")"

        return __repr__string
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
        cls_args = list(signature(Message).parameters)
        __repr__string = [f"{self.__class__.__name__}("]
        [__repr__string.append(f"{arg}={getattr(self, arg)}, ") for arg in cls_args if arg != "self"]

        __repr__string = "".join(__repr__string)
        __repr__string = __repr__string[:-2] + ")"

        return __repr__string

    def __init__(self, message: str=None, file: File=None, sender: IPAddress=None):
        self.message = message
        self.file = file
        self.sender = sender

        super().__init__()

if __name__ == '__main__':
    file_obj = Message("Hello World.", None, None)

    print(file_obj)

import io
from typing import Union
from inspect import signature

def make__repr__(cls, ins) -> str:
    cls_args = list(signature(cls).parameters)
    __repr__string = [f"{ins.__class__.__name__}("]
    [__repr__string.append(f"{arg}={getattr(ins, arg)}, ") for arg in cls_args if arg != "self" and hasattr(ins, arg)]

    __repr__string = "".join(__repr__string)
    __repr__string = __repr__string[:-2] + ")"

    return __repr__string

class IPAddress(object):
    pass

class File(object):
    """Represents a File to be send over a network."""

    def __repr__(self) -> str:
        return make__repr__(File, self)
        
    def __init__(self, file, mode) -> None:
        self.file = open(file, mode)

        super().__init__()

    def data(self) -> Union[bytes, str]:
        """Returns the file object data."""
        return self.file.read()

class Message(object):
    """Represents a Message to be send over a network."""

    def __repr__(self) -> str:
        """
        cls_args = list(signature(Message).parameters)
        __repr__string = [f"{self.__class__.__name__}("]
        [__repr__string.append(f"{arg}={getattr(self, arg)}, ") for arg in cls_args if arg != "self"]

        __repr__string = "".join(__repr__string)
        __repr__string = __repr__string[:-2] + ")"

        return __repr__string
        """

        return make__repr__(Message, self)

    def __init__(self, message: Union[str, int, None]=None, file: File=None, sender: IPAddress=None):
        self.message = message
        self.file = file
        self.sender = sender

        super().__init__()

if __name__ == '__main__':
    file_obj = Message("Hello World.", File("demo_file.py", 'r'), None)

    print(file_obj)

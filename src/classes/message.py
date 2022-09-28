
from typing import Union as _Union
from inspect import signature

MESSAGE = 0
HEATBEAT = 1

def __make__repr__(cls, ins) -> str:
    cls_args = list(signature(cls).parameters)
    __repr__string = [f"{ins.__class__.__name__}("]
    [__repr__string.append(f"{arg}={getattr(ins, arg)}, ") for arg in cls_args if arg != "self" and hasattr(ins, arg)]

    __repr__string = "".join(__repr__string)
    __repr__string = __repr__string[:-2] + ")"

    return __repr__string

class IPAddress(object):
    pass

class Message(object):
    """Represents a Message to be send over a network."""

    def __repr__(self) -> str:
        return __make__repr__(Message, self)

    def __init__(self, message: _Union[str, int, None]=None, type: int=0, sender: IPAddress=None):
        self.message = message
        self.type = type
        self.sender = sender

        super().__init__()


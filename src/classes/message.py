import sys, io

class Message(str):
    """Represents a Message to be send over a network."""

    def __repr__(self) -> str:
        return self

    def __str__(self) -> str:
        return f"Message(str={super().__str__()}, file={self.file})"

    def __new__(cls, *args, **kwargs):
        cls.file: io.FileIO = kwargs['file']
        del kwargs['file']

        print(cls.file)

        return str.__new__(cls, *args, **kwargs)

    def size(self) -> int:
        return sys.getsizeof(self)
    
    def in_bytes(self) -> bytes:
        return self.encode()
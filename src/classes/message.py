import sys, io

class File(object):
    """Represents a File to be send over a network."""
    def __new__(cls, *args, **kwargs) -> io.TextIOWrapper:
        return super().__init__(*args, **kwargs)
    
    def __init__(self, *args, **kwargs):
        pass


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

if __name__ == '__main__':
    file_obj = File('demo_file.py', 'rb')
    print(file_obj.what_is_self())
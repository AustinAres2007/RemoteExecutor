import socket, os, sys, io

SERVER_HOST: str = "demp.ddns.net"
SERVER_PORT: int = 2022

# TODO: handle file sending

class Message(str):

    def __repr__(self) -> str:
        return self.string

    def __str__(self) -> str:
        return f"Message(str={self.string})"

    def __init__(self, string: str, file: io.FileIO):
        self.string = string
        self.file = file
    
    def size(self) -> int:
        return sys.getsizeof(self.string)
    
    def in_bytes(self) -> bytes:
        return self.string.encode()

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as re_client:

        def close():
            re_client.close()
            sys.exit(0)

        re_client.connect((SERVER_HOST, SERVER_PORT))
        commands = {
                "exit": lambda: close(),
                "status": lambda: None,
                "shutdown": lambda: None,
                "project": lambda: None
        }
        client_side_only = ['exit']

        while True:
            try:

                command = input(f"Send to {SERVER_HOST}:{SERVER_PORT} >>> ")

            
                commands[command]()
                if command not in client_side_only:
                    re_client.sendall(command.encode())
                    reply = re_client.recv(1024).decode('utf-8')
                    print(reply)

            except KeyError:
                print(f"{command} is not a client command.")
            except KeyboardInterrupt:
                sys.exit(0)

if __name__ == "__main__":
    main()

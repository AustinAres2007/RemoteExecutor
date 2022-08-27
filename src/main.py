import socket, sys
from typing import *

# I do not bother to use asyncio. This is meant for one connection at a time.

def main():
    HOST = PORT = None
    try:
        HOST = sys.argv[1]
        PORT = int(sys.argv[2])
    except IndexError:
        return print("Missing Arguments")
    else:
        print(f"~ Details ~\n\nHost IP: {HOST}\nHost Port: {PORT}\n\n")
        with RemoteExecutor(socket.AF_INET, socket.SOCK_STREAM) as code_host:
            code_host.bind((HOST, PORT))
            code_host.listen(1)

            print('Host listening for incoming connections.')

            code_host.start()

# TODO: Handle client error handling (Here)

class Client(socket.socket):
    def __init__(self, client: socket.socket):
        self.client = client

class RemoteExecutor(socket.socket):
    def __init__(self, *args, **kwargs):
        self.command_list = {
            "project": self.file_transfer,
            "exit": self._close_client
        }
        super().__init__(*args, **kwargs)

    def __str__(self):
        return f"RemoteExecutor(host={self.host}, port={self.port})"

    def file_transfer(self, command: str, client: Client) -> list[Any, str]:
        pass
    
    def _close_client(self, cmd: str, client: Client):
        client.close()
        client = None

    def process_client(self, client: socket.socket) -> list[str, str]:
        command = client.recv(1024).decode('utf-8')
        
        try:
            process, reply = self.command_list[command](command, client)
        except KeyError:
            reply = "Command does not exist."
        
        return [command, reply]
    
    def start(self) -> None:
        while True:
            client, addr = super().accept()
            client = Client(client).client

            print(client.__str__())

            print(f"Connection from {addr}")

            while client:
                command, reply = self.process_client(client=client)
                client.sendall(reply.encode())
            
if __name__ == "__main__":
    main()

        
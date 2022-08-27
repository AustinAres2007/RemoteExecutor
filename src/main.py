import socket, threading
from typing import *

# I do not bother to use asyncio. This is meant for one connection at a time.

HOST = "192.168.1.227"
PORT = 2022
RUN = True

# TODO: Handle client error handling (Here)

class RemoteExecutor(socket.socket):
    def __init__(self, *args, **kwargs):
        self.command_list = {
            "project": self.file_transfer
        }
        super().__init__(*args, **kwargs)

    def __str__(self):
        return f"RemoteExecutor(host={self.host}, port={self.port})"

    def file_transfer(self, command, client) -> list[Any, str]:
        client.sendall(b'wf')

        with open("TEST.txt", 'wb+') as file_to_write:
            while True:
                chunk = client.recv(4096)
                print(chunk)
                if chunk:
                    file_to_write.write(chunk)
                else:
                    break

    def process_client(self, client: socket.socket) -> list[str, str]:
        command = client.recv(1024).decode('utf-8')
        
        try:
            process, reply = self.command_list[command](command, client)
        except KeyError:
            reply = "Command does not exist."
        
        return [command, reply]
    
    def relationship(self) -> None:
        while RUN:
            client, addr = super().accept()
            command = None

            print(f"Connection from {addr}")

            while command != 'terminate':
                command, reply = self.process_client(client=client)
                client.sendall(reply.encode())
            else:
                print(f"Connection terminated by {addr}")
                client.close()
        
    
with RemoteExecutor(socket.AF_INET, socket.SOCK_STREAM) as code_host:
    code_host.bind((HOST, PORT))
    code_host.listen(1)
    code_host.relationship()


        
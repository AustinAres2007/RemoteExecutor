import socket, sys, pickle
from typing import *
from classes.message import Message, File 

# Don't use this code if you do not like having risks. This script uses Pickle to send class objects.
# Use at your own risk. (Similar risks to using eval() or exec())

# I do not bother to use asyncio. This is meant for one connection at a time.


def main():

    HOST = PORT = None
    try:
        print(sys.argv)
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

class RemoteExecutor(socket.socket):
    def __str__(self) -> str:
        return f"RemoteExecutor(host={self.host}, port={self.port})"

    def __init__(self, *args, **kwargs):
        self.command_list = {
            "project": self.file_transfer,
            "shutdown": lambda *args: self.close(),
            "status": lambda *args: self.status()

        }
        super().__init__(*args, **kwargs)

    def status(self) -> str:
        return "200"

    def file_transfer(self, command: str, client: socket.socket) -> str:
        return "This command is not finished."

    def process_client(self, client: socket.socket) -> str:
        command = client.recv(1024).decode('utf-8')
        
        try:
            reply = self.command_list[command](command, client)
        except KeyError:
            reply = "Command does not exist."
        
        return reply
    
    def start(self) -> None:
        while True:
            try:
                client, addr = super().accept()
                print(f"Connection from {addr[0]}")

                while client:
                    try:
                        reply = Message(self.process_client(client=client), None)
                        client.sendall(pickle.dumps(reply))
                    except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
                        print("Client connection Error, disconnecting client.")
                        client = None
                    except AttributeError:
                        sys.exit(0)
            except OSError:
                continue

if __name__ == "__main__":
    main()

        

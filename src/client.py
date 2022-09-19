from curses.ascii import isdigit
import socket, os, sys, io, pickle
from classes.message import Message, File
from threading import Thread
# TODO: handle file sending
def error(string):
    return print(string); sys.exit(1)

def main():
    # Opens a line of communication between client and host.
    def listen_for_messages():
        buffer_size = 512*512

        while True:
            reply_data = re_client.recv(buffer_size)
            reply = pickle.loads(reply_data)
            print(f"\n{reply.message}")

    try:
        SERVER_HOST: str = sys.argv[1]
        SERVER_PORT: int = int(sys.argv[2])
    except IndexError:
        return error("Not enough parameters in run arguments.")
    except ValueError:
        return error("The port parameter is a string type, not integer. (File Argument format: <host-ip> <port>)")
    else:
            
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as re_client:
            try:
    
                re_client.connect((SERVER_HOST, SERVER_PORT))
                commands = {
                        "status": (lambda: None, False),
                        "clone": (lambda: None, False),
                        "echo": (lambda: None, False),
                        "exit": (lambda: None, False),
                        "sys": (lambda: None, False),
                        "rm": (lambda: None, False),
                        "run": (lambda: None, False)
                }
                
            except (ConnectionRefusedError, ConnectionError):
                return error("Server refused connection / the server does not exist.")
            
            else:
                message_thread = Thread(target=listen_for_messages)
                message_thread.start()

                while True:
                    try:
                        command_name = input(f"Send to {SERVER_HOST}:{SERVER_PORT} >>> ")
                        command = commands[command_name.split(' ')[0]]
                        command[0]()

                        if not command[1]:
                            re_client.sendall(command_name.encode())
        
                    except KeyboardInterrupt:
                        return error("Shutting down client.")
                    except KeyError:
                        print("Specified command does not exist.")

if __name__ == "__main__":
    main()

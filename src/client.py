import socket, sys, pickle
from classes.message import Message, File
from threading import Thread
from os import system

# TODO: handle file sending
def error(string):
    return print(string); sys.exit(1)

system('clear')

def main():
    global stop
    stop = False
    # Opens a line of communication between client and host.
    def listen_for_messages():
        buffer_size = 512*512
        stop = False
        while not stop:
            try:
                reply_data = re_client.recv(buffer_size)
                reply = pickle.loads(reply_data)
                print(reply.message)
            except OSError:
                stop = True
            except EOFError:
                return exit_prog()
    try:
        SERVER_HOST: str = sys.argv[1]
        SERVER_PORT: int = int(sys.argv[2])
    except IndexError:
        return error("Not enough parameters in run arguments.")
    except ValueError:
        return error("The port parameter is a string type, not integer. (File Argument format: <host-ip> <port>)")
    else:
        def exit_prog():
            re_client.sendall("!".encode())
            return re_client.close()
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as re_client:
            try:
    
                re_client.connect((SERVER_HOST, SERVER_PORT))
                commands = {
                        "status": (lambda: None, False),
                        "clone": (lambda: None, False),
                        "sys": (lambda: None, False),
                        "rm": (lambda: None, False),
                        "exit": (lambda: exit_prog(), True),
                        "run": (lambda: None, False),
                        "help": (lambda: None, False),
                        "terminate": (lambda: None, False),
                        "repos": (lambda: None, False)
                }
                
            except (ConnectionRefusedError, ConnectionError):
                return error("Server refused connection / the server does not exist.")
            
            else:
                message_thread = Thread(target=listen_for_messages)
                message_thread.start()

                while not stop:
                    try:
                        command_name = input()
                        command = commands[command_name.split(' ')[0]]
                        command[0]()

                        if not command[1]:
                            re_client.sendall(command_name.encode())
                        else:
                            stop = True
        
                    except KeyboardInterrupt:
                        exit_prog()
                        return error("Shutting down client.")
                    except KeyError:
                        print("\nSpecified command does not exist.\n")

if __name__ == "__main__":
    main()

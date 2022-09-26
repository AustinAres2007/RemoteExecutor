import socket, sys, pickle, json
from classes.message import Message, File
from threading import Thread
from os import system

system('clear')

BUFFER = 4096
__VERSION__ = 1.2
COMMAND_INPUT_NOTIF = "\n> "

os_errors = {
    9: "Host closed."
}
def error(string):
    print(string)
    return sys.exit(1)

class RemoteExecutorClient:

    def exit_prog(self):    
        try:    
            self.host.send("!".encode())
            self.host.close()
        except:
            pass

    def send(self, message: str):
        try:
            self.host.sendall(str(message if message else ".").encode())
        except OSError as osr:
            return error(os_errors[osr.errno])

    def connection_protocol(self):
        try:
            self.send(__VERSION__)
            version_conf = self.host.recv(BUFFER).decode()

            if version_conf != 'True':
                self.exit_prog()
                return error(version_conf)
            elif version_conf not in ["Incorrect client version.", "True"]:
                print(">>",version_conf)

            self.send(input("Host Password (If not needed, press enter): "))
            password_conf = self.host.recv(BUFFER).decode()

            if password_conf != 'True':
                self.exit_prog()
                return error("Incorrect host password.")
            
            return True
        except KeyboardInterrupt:
            self.exit_prog()
        except ConnectionResetError:
            return sys.exit(1)

    def listen_for_messages(self):
        buffer_size = 512*512
        stop = False

        while not stop:
            try:
                reply_data = self.host.recv(buffer_size)
                reply: Message = pickle.loads(reply_data)
                print(reply.message, end=COMMAND_INPUT_NOTIF)
            except OSError:
                stop = True
            except EOFError:
                return self.exit_prog()
            except pickle.UnpicklingError:
                return sys.exit(1)
    
    def listen_for_commands(self):
        try:
            SERVER_HOST: str = sys.argv[1]
            SERVER_PORT: int = int(sys.argv[2])
        except IndexError:
            return error("Not enough parameters in run arguments.")
        except ValueError:
            return error("The port parameter is a string type, not integer. (File Argument format: <host-ip> <port>)")
        else:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as re_client:
                self.host = re_client
                try:
        
                    self.host.connect((SERVER_HOST, SERVER_PORT))
                    commands = {
                            "status": (lambda: None, False),
                            "clone": (lambda: None, False),
                            "sys": (lambda: None, False),
                            "rm": (lambda: None, False),
                            "exit": (lambda: self.exit_prog(), True),
                            "run": (lambda: None, False),
                            "help": (lambda: None, False),
                            "terminate": (lambda: None, False),
                            "repos": (lambda: None, False),
                            "pkg": (lambda: None, False),
                            "dall": (lambda: None, False)
                    }
                    
                except (ConnectionRefusedError, ConnectionError):
                    return error("Server refused connection / the server does not exist.")
                
                else:
                    con = self.connection_protocol()
                    stop = False

                    if con:
                        message_thread = Thread(target=self.listen_for_messages)
                        message_thread.start()

                        while not stop:
                            try:
                                command_name = input()
                                command = commands[command_name.split(' ')[0]]
                                command[0]()

                                if not command[1]:
                                    self.send(command_name)
                                else:
                                    stop = True      
                            except KeyboardInterrupt:
                                self.exit_prog()
                                return error("Shutting down client.")
                            except KeyError:
                                print("\nSpecified command does not exist.", end=COMMAND_INPUT_NOTIF)

                            except UnboundLocalError:
                                return
                    else:
                        return

if __name__ == "__main__":
    RemoteExecutorClient().listen_for_commands()

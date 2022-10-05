import socket, sys, pickle, time
from threading import Thread
from os import system

from urllib3 import connection_from_url

system('clear')

def error(string):
    print(string)
    return sys.exit(1)

SHUTDOWN_ACK = "shutdown_ack"
HEARTBEAT_ACK = "heartbeat_ack"
BUFFER = 4096
__VERSION__ = 1.3
COMMAND_INPUT_NOTIF = "\n> "

SERVER_HOST: str = sys.argv[1]
SERVER_PORT: int = int(sys.argv[2])

if not (SERVER_PORT > 0 and SERVER_PORT <= 65535):
    error("Please chose a port between 1 - 65535")

os_errors = {
    #9: "Closed.",
    32: "Disconnected from host, the host either crashed or you lost connection. Try again."
}

class RemoteExecutorClient:

    def __init__(self, debug: bool=False, module=False):
        self.module = module
        self.debug = debug
        self.stop = False

    def exit_prog(self):    
        try:    
            self.send(SHUTDOWN_ACK)
            self.host.close()
        except:
            pass

    def send(self, message: str):
        try:
            self.host.sendall(str(message if message else ".").encode())
        except OSError as osr:
            return error(os_errors[osr.errno])

    def connection_protocol(self):
        # TODO: Support online client input (Only stdin right now)

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as re_client:
            self.host = re_client
            try:
                self.host.connect((SERVER_HOST, SERVER_PORT))
            except (ConnectionRefusedError, ConnectionError):
                return error("Server refused connection / the server does not exist.")

        try:
            print(f"Sending {__VERSION__} as client version.")
            self.send(__VERSION__)
            version_conf = self.host.recv(BUFFER).decode()

            if version_conf != 'True':
                self.exit_prog()
                return error(version_conf)
            elif version_conf not in ["Incorrect client version.", "True"]:
                print(version_conf)

            self.send(input("Host Password (If not needed, press enter): "))
            password_conf = self.host.recv(BUFFER).decode()

            if password_conf != 'True':
                self.exit_prog()
                return error("Incorrect host password.")
            
            return True

        except KeyboardInterrupt as kbi:
            if not self.module:
                return self.exit_prog()
            else:
                raise kbi

        except ConnectionResetError as cre:
            if not self.module:
                return sys.exit(1)
            else:
                raise cre

    def heartbeat_rythm(self):
        while self.stop:
            for _ in range(25):
                time.sleep(1)

            self.send(HEARTBEAT_ACK)

    def listen_for_messages(self):
        buffer_size = 512*512
        self.stop = False

        while not self.stop:
            try:
                reply = pickle.loads(self.host.recv(buffer_size))
                print(reply.message)
                    
            except OSError:
                self.stop = True
            except EOFError:
                return self.exit_prog()
            except pickle.UnpicklingError:
                return sys.exit(1)
    
    def listen_for_commands(self):
        connection_status = self.connection_protocol()
        print(connection_status)
        
        if connection_from_url == True:
            
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
                        "pkg": (lambda: None, False)
            }
                
            message_thread = Thread(target=self.listen_for_messages)
            message_thread.start()
            pulse_thread = Thread(target=self.heartbeat_rythm)
            pulse_thread.start()

            if not self.module:            
                while not self.stop:
                    try:
                        time.sleep(.5)
                        command_name = input()
                        command = commands[command_name.split(' ')[0]]
                        command[0]()

                        if not command[1]:
                            self.send(command_name)
                        else:
                            print("Ending")
                            self.stop = True      
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
    try:
        RemoteExecutorClient(bool(int(sys.argv[3]))).listen_for_commands()
    except (IndexError, ValueError):
        print("Missing Command line arguments. (<IP> <PORT> <DEBUG || 1 / 0>)")
else:... # Online client init code
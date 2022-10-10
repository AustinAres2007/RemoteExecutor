import socket, time
from threading import Thread as _Thread
from typing import Callable, Union as _Union

class RemoteExecutorError(Exception):
    def __init__(self, error, errno: int):
        self.error = error
        self.errno = errno

        super().__init__(f"{error} [Error number: {errno}]")


class RemoteExecutorClient:

    def __exit__(self, _exc_type, _exc_value, _exc_traceback):
        self.disconnect()
    
    def __enter__(self):
        self.connect()
        return self

    def __init__(self, address: str, port: int, password: _Union[str, None]=None) -> None:
        """
        Remote Executor Client
        """

        self.__os_errors__ = {
            9: "Closed.",
            32: "Disconnected from host, the host either crashed or you lost connection. Try again."
        }
        self.__api_errors__ = {
            1: "Cannot run module directly.",
            2: "Incomplete server reply. (PickleError)",
            3: "Connection was reset, closed, or abandoned by host.",
            4: "Incorrect Password.",
            5: "Incorrect Client Version.",
            6: "General network issue.",
            7: "Host does not exist.",
            8: "Command does not exist."
        }

        self.commands = {
            "status": (lambda: None, False),
            "clone": (lambda: None, False),
            "sys": (lambda: None, False),
            "rm": (lambda: None, False),
            "exit": (lambda: self.disconnect(), True),
            "run": (lambda: None, False),
            "help": (lambda: None, False),
            "terminate": (lambda: None, False),
            "repos": (lambda: None, False),
            "pkg": (lambda: None, False)
        }

        if not (int(port) > 0 and int(port) <= 65535):
            raise RemoteExecutorError(self.__api_errors__[7], 7)

        self.address = address
        self.port = port
        self.password = password

        self.__STOP__ = False
        self.__SHUTDOWN_ACK__ = "shutdown_ack"
        self.__HEARTBEAT_ACK__ = "heartbeat_ack"
        self.__TERMINATE_MSG_ACK__ = "terminate_msg_ack"
        self.__BUFFER__ = 4096
        self.__VERSION__ = "1.3"

    def __send__(self, message: _Union[str, None]) -> None:
        try:
            self.host.sendall(str(message if message else ".").encode())
        except OSError as osr:
            raise RemoteExecutorError(self.__os_errors__[osr.errno], 6)

    def __connection_protocol__(self) -> _Union[bool, None]:
        try:
            self.__send__(self.__VERSION__)
            version_conf = self.host.recv(self.__BUFFER__).decode()

            if version_conf != 'True':
                raise RemoteExecutorError(self.__api_errors__[5], 5)
            
            if not self.password:   
                self.password = self.password if self.password else '.'

            self.__send__(self.password)
            password_conf = self.host.recv(self.__BUFFER__).decode()

            if password_conf != 'True':
                raise RemoteExecutorError(self.__api_errors__[4], 4)
            
            print(self.host.recv(self.__BUFFER__).decode().split(self.__TERMINATE_MSG_ACK__)[0])

            return True

        except ConnectionResetError:
            raise RemoteExecutorError(self.__api_errors__[3], 3)
        except ValueError:
            raise RemoteExecutorError(self.__api_errors__[7], 7)

    def __heartbeat_rythm__(self) -> None:
        while self.__STOP__:
            for _ in range(25):
                time.sleep(1)

            self.__send__(self.__HEARTBEAT_ACK__)

    def __recieve_output__(self) -> str:
        OUT = ""
        try:
            data = self.host.recv(512*512)
            OUT = data.decode().strip()
        except:
            pass
        finally:
            return OUT

    def connect(self) -> socket.socket:
        self.host = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host.connect((self.address, self.port))
        self.host.settimeout(5.0)

        self.__connection_protocol__()
        return self.host
        
    def disconnect(self) -> None:    
        try:    
            self.__send__(self.__SHUTDOWN_ACK__)
            self.host.close()
            self.host = None
        except:
            pass

    def send_command(self, command: str, handle_f: _Union[Callable, None], ignore_unknown=False, blocking: bool=True) -> None:
        try:
            def __handle_command():
                command_func = self.commands[command.split(" ")[0]]
                command_func[0]()

                if not command_func[1]:
                    self.__send__(command)

                while not self.__STOP__ and self.host:
                    cmd_return: str = self.__recieve_output__()

                    if isinstance(handle_f, Callable):
                        handle_f(cmd_return.split(self.__TERMINATE_MSG_ACK__)[0])

                    if self.__TERMINATE_MSG_ACK__ in cmd_return:
                        break
                
                else:
                    raise RemoteExecutorError(self.__api_errors__[3], 3)
            
            __handle_command() if blocking else _Thread(target=__handle_command).start()
        except KeyError:
            if not ignore_unknown:
                raise RemoteExecutorError(self.__api_errors__[8], 8)
            
        
"""
Communicates with the RemoteExecutor server, every function in the client API is based off the send_command function. 
All functions here are basically shortcuts
"""

import socket, time
from threading import Thread as _Thread
from typing import Any, Callable, Union as _Union

DEFAULT = print
RETURNED = lambda msg: msg

class RemoteExecutorError(Exception):
    def __init__(self, error, errno: int):
        self.error = error
        self.errno = errno

        super().__init__(f"{error} [Error number: {errno}]")


class RemoteExecutorClient:

    def __exit__(self, _exc_type, _exc_value, _exc_traceback):
        self.disconnect()
    
    def __enter__(self):
        return self

    def __init__(self, address: str, port: int, password: _Union[str, None]=None, output_function: _Union[Callable, None]=DEFAULT, with_ack=False, with_welcome=False) -> None:
        """
        Remote Executor Client

        Connects to host automatically, you can disconnect with the client.disconnect() function.
        You may connect back manually with the connect() function.

        ### Parameters
        #### address : str
            * RemoteExecutor address to connect to.
        #### port : int
            * Port to connect to.
        #### password : str | None (default: None)
            * Password for RemoteExecutor instance.
        #### output_function : Callable | None (default: client.DEFAULT)
            * Function to call when STDOUT data is recieved from RemoteExecutor. (1 required argument)
        

        """

        self.__os_errors__ = {
            9: "Closed.",
            32: "Disconnected from host, the host either crashed or you lost connection. Try again."
        }
        self.__api_errors__ = {
            1: "Cannot run module directly.",
            2: "Incomplete server reply. (PickleError)",
            3: "Connection was reset or closed. Or the connection was abandoned by host.",
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
            "pkg": (lambda: None, False),
            "cd": (lambda: None, False)
        }

        if not (int(port) > 0 and int(port) <= 65535):
            raise RemoteExecutorError(self.__api_errors__[7], 7)

        self.address = address
        self.port = port
        self.password = password
        self.output_function = output_function
        self.host = None
        self.welcome = with_welcome

        self.__HEARTBEAT_ENABLED = with_ack
        self.__STOP__ = False
        self.__SHUTDOWN_ACK__ = "shutdown_ack"
        self.__HEARTBEAT_ACK__ = "heartbeat_ack"
        self.__TERMINATE_MSG_ACK__ = "terminate_msg_ack"
        self.__BUFFER__ = 4096
        self.__VERSION__ = "1.4"

        self.connect()

    def __send__(self, message: _Union[str, None]=None) -> None:
        """
        Sends raw bytes to RemoteExecutor.
        
        ## Parameters
        #### message : str | None (default: None)

        ## Raises
        #### OSError
            Occurs when the connection dies or fails to send in any way.
        #### BrokenPipeError
            Occurs when the host suddenly dies.
        """
        if self.host:
            return self.host.sendall(str(message if message else ".").encode())
        raise RemoteExecutorError(self.__api_errors__[3], 3)

    def __connection_protocol__(self) -> _Union[bool, None]:
        """
        Authenticates connection to RemoteExecutor
        
        ## No Parameters
        ## Returns : bool | None
        ## Raises
        #### ConnectionResetError
            Occurs when the connection dies or fails to send in any way.
        #### RemoteExecutorError
            (7) Occurs when the host does not exist.
            (5) The client version is too old.
            (4) The password entered is incorrect.
        #### TimeoutError
            Occurs when the client did not recvieve host data.
        """
        try:
            version_conf = self.__send_and_recieve__(self.__VERSION__, 1, RETURNED, True)

            if version_conf != 'True':
                raise RemoteExecutorError(self.__api_errors__[5], 5)
            
            if not self.password:   
                self.password = self.password if self.password else '.'

            password_conf = self.__send_and_recieve__(self.password, 1, RETURNED, True)

            if password_conf != 'True':
                raise RemoteExecutorError(self.__api_errors__[4], 4)
            
            welcome_msg = self.host.recv(self.__BUFFER__).decode().split(self.__TERMINATE_MSG_ACK__)[0]
            if self.welcome:
                print(welcome_msg)

            if self.__HEARTBEAT_ENABLED:
                _Thread(target=self.__heartbeat_rythm__).start()

            return True

        except ValueError:
            raise RemoteExecutorError(self.__api_errors__[7], 7)

    def __heartbeat_rythm__(self) -> None:
        """
        Keeps the connection to RemoteExecutor alive.
        Sends a signal to the host every 25 seconds, if signal
        is not recieved by the host, it is disconnected.
        
        ## No Parameters
        ## Raises
        #### TimeoutError
            Occurs when the signal fails to send.
        """

        
        while not self.__STOP__:
            time.sleep(25)
            self.__send__(self.__HEARTBEAT_ACK__)

    def __recieve_output__(self) -> str:
        """
        Waits for STDOUT / STDERR data from RemoteExecutor.
        There is a 10 second timeout.

        ## No Parameters
        ## Returns : str
        ## Raises
        #### TimeoutError
            Occurs when the signal fails to send.
        """
        data = self.host.recv(512*512)
        return data.decode().strip()

    def __send_and_recieve__(self, message: _Union[str, None]=None, buffer: int=-1, output_function: _Union[Callable, None]=None, return_value: bool=False) -> _Union[Any, None]:
        """
        Combines __send__() and __recieve_output__()
        Sends data to RemoteExecutor, and recieves STDOUT / STDERR 
        data until __TERMINATE_MSG_ACK__ is recieved.

        Authors Note: Nested anon functions and functions for days!

        ## Parameters
        #### message : str | None (default=None)
            Data to send to RemoteExecutor
        #### buffer : int (default=-1)
            Will stop reading data from RemoteExecutor after specified amount of messages, if set to -1, there is no limit until __TERMINATE_MSG_ACK__ is read.
        #### output_function : Callable | None (default: RemoteExecutorClient.output_function)
            Function to call when data is recieved from RemoteExecutor. If none, it will use the one specified in the initialised classmethod.
        #### return_value : bool (default: False)
            After receiving a single message, it will return the value returned by the specified output_function (local). Use client.RETURNED for a normal returned value with no parsing.
        ## Returns : Any | None
        ## Raises
        #### TimeoutError
            Occurs when data cannot be send or recieved.
        #### RemoteExecutorError
            Occurs when the host is closed.
        """
        if output_function == None:
            output_function = self.output_function

        self.__send__(message)
        reply_count = 0

        while not self.__STOP__ and self.host:
            cmd_return: str = self.__recieve_output__()
            out_func = lambda: output_function(cmd_return.split(self.__TERMINATE_MSG_ACK__)[0])

            if isinstance(output_function, Callable):
                if return_value:
                    return out_func()
                out_func()

            if self.__TERMINATE_MSG_ACK__ in cmd_return or reply_count == buffer:
                break
        
        else:
            raise RemoteExecutorError(self.__api_errors__[3], 3)


    def connect(self) -> socket.socket:
        """
        Esablishes connection to RemoteExecutor.
        
        ## No Parameters
        ## Returns : None
        ## Raises
        #### ConnectionRefusedError
            Occurs when the specified RemoteExecutor host does not exist.
        """

        if not isinstance(self.host, socket.socket):
            self.host = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.host.connect((self.address, self.port))
            self.host.settimeout(5.0)

            self.__connection_protocol__()
            return self.host
        
    def disconnect(self) -> None:    
        """
        Disconnects from RemoteExecutor.
        
        ## No Parameters
        ## Returns : None
        ## Raises
        #### OSError
            Occurs when the connection dies or fails to send in any way.
        #### BrokenPipeError
            Occurs when the host suddenly dies.
        """

        self.__send__(self.__SHUTDOWN_ACK__)
        self.host.close()
        self.host = None

    def send_command(self, command: str, ignore_unknown=False, blocking: bool=True) -> None:
        """
        Sends a command to RemoteExecutor. See full command list with "help"
        
        ## Parameters
        #### command : str
            The command to send to RemoteExecutor
        #### ignore_unknown : bool (default: False)
            Does not raise an error when the command is unknown, if set to True
        #### blocking : bool (default: True)
            If True, function will only return once finished recieving data from RemoteExecutor
        ## Returns : None
        ## Raises
        #### RemoteExecutorError
            Occurs when a command is not registered with self.commands and ignore_unknown is True
        #### TimeoutError
            Occurs when data cannot be send or recieved.
        #### RemoteExecutorError
            Occurs when the host is closed. 
        """
        try:
            def __handle_command():
                command_func = self.commands[command.split(" ")[0]]
                command_func[0]()

                if not command_func[1]:
                    self.__send_and_recieve__(command)


            __handle_command() if blocking else _Thread(target=__handle_command).start()
    
        except KeyError:
            if not ignore_unknown:
                raise RemoteExecutorError(self.__api_errors__[8], 8)
    
    def change_terminal_directory(self, path: str):
        """
        Changes directory used in the sys command.
        
        ## Parameters
        #### path : str
            The directory to travel to.
        ## Returns : None
        ## Raises
        #### TimeoutError
            Occurs when data cannot be send or recieved.
        #### RemoteExecutorError
            Occurs when the host is closed. 
        """
        self.__send_and_recieve__(f"cd {path}")
    
    def git(self, command: str):
        """
        Accesses Git without having to use "sys git" with send_command

        ## Parameters
        #### commands : str
            The git command(s) to send to RemoteExecutor
        ## Returns : None
        ## Raises
        #### TimeoutError
            Occurs when data cannot be send or recieved.
        #### RemoteExecutorError
            Occurs when the host is closed. 
        """
        command_split = command.split(" ")
        command_split.insert(0, "git") if command_split[0] != "git" else None

        self.__send_and_recieve__(f"sys {' '.join(command_split)}")
    
    def get_repos(self):
        """
        Gets a list of all repositories that belong to the RemoteExecutor
        
        ## No Parameters
        """
        repos = self.__send_and_recieve__("repos", -1, RETURNED, True)
        return repos.split("\n")
    
    def clone_repo(self, repo_link: str, folder: str):
        """
        Clones a repository from specified link.
        
        ## Parameters
        #### repo_link : str
            The link to clone from.
        #### folder : str
            The folder to clone repository to.
        ## Returns : None
        ## Raises
        #### TimeoutError
            Occurs when data cannot be send or recieved.
        #### RemoteExecutorError
            Occurs when the host is closed. 
        """

        self.__send_and_recieve__(f"clone {repo_link} {folder}")
    
    def remove_repo(self, local_folder: str):
        """
        Removes a local repository.
        
        ## Parameters
        #### local_folder : str
            The path to the local repository (Relative to the src/scripts folder located within RemoteExecutor)
        ## Returns : None
        ## Raises
        #### TimeoutError
            Occurs when data cannot be send or recieved.
        #### RemoteExecutorError
            Occurs when the host is closed. 
        """

        self.__send_and_recieve__(f"rm {local_folder}")
    
    def run_repo(self, path_to_executable: str):
        """
        Executes a script with the given path (Relative to the src/scripts folder located within RemoteExecutor)
        
        ## Parameters
        #### path_to_executable : str
            Path to the executable you want to execute.(Relative to src/scripts)
        ## Returns : None
        ## Raises
        #### TimeoutError
            Occurs when data cannot be send or recieved.
        #### RemoteExecutorError
            Occurs when the host is closed. 
        """

        self.__send_and_recieve__(f"run {path_to_executable}")
    
    def terminate_repo(self):
        """
        Terminates execution of the running script, does help if there is an input which is blocking execution. (
        (Note: inputs are NOT allowed with RemoteExecutor due to the lack of STDIN, if you add any, the code will freeze, but never actually crash)

        ## No Parameters
        ## Returns : None
        ## Raises
        #### TimeoutError
            Occurs when data cannot be send or recieved.
        #### RemoteExecutorError
            Occurs when the host is closed. 
        """

        self.__send_and_recieve__("terminate")
    
    def install_package(self, repo: str, package: str):
        """
        Installs a package for the specified repository.
        
        ## Parameters
        #### repo : str
            The repository to install the package to.
        #### package : str
            The package to install, uses the same names as pip.
        ## Returns : None
        ## Raises
        #### TimeoutError
            Occurs when data cannot be send or recieved.
        #### RemoteExecutorError
            Occurs when the host is closed. 
        """
        
        self.__send_and_recieve__(f"pkg install {package} {repo}")
    
    def uninstall_package(self, repo: str, package: str):
        """
        Uninstalls a package from the specified repository.
        
        ## Parameters
        #### repo : str
            The repository to uninstall the package from
        #### package : str
            The package to uninstall, uses the same names as pip, and others.
        ## Returns : None
        #### TimeoutError
            Occurs when data cannot be send or recieved.
        #### RemoteExecutorError
            Occurs when the host is closed. 
        """

        self.__send_and_recieve__(f"pkg uninstall {package} {repo}")
    
    def show_packages(self, repo: str) -> list:
        """
        Show the installed packages for the specified repository.
        
        ## Parameters
        #### repo : str
            The repository to show the installed packages from.
        ## Returns : list[str, ...]
        ## Raises 
        #### TimeoutError
            Occurs when data cannot be send or recieved.
        #### RemoteExecutorError
            Occurs when the host is closed. 
        """
        packages = self.__send_and_recieve__(f"pkg show {repo} .", -1, RETURNED, True)
        return [pkg.split(" ")[0] for pkg in packages.split("\n") if pkg]




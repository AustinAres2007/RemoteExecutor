import socket, sys, pickle, os, shutil, subprocess, time, git, config
from struct import pack
from typing import *
from classes.message import *
from git import Repo
from threading import Thread

config_object = config.Config("src/host-config.cfg")

# Don't use this code if you do not like having risks. This script uses Pickle to send class objects.
# Use at your own risk. (Similar risks to using eval() or exec())

# I do not bother to use asyncio. This is meant for one connection at a time.
errors = {
    0: "Missing Arguments.",
    1: "Unknown Error.",
    2: "No repo with that name."
}

allowed_commands = [
                "ls",
                "ifconfig",
                "pwd",
                "pip",
                "touch",
                "source"
]

__AUTHOR__ = "Navid Rohim"

nl = "\n"
file = open("src/connection_message.txt")
conn_message = file.read()
file.close()

def main():

    try:
        HOST, PORT = sys.argv[1:]
        PORT = int(PORT)
    except ValueError:
        return print("Port is a String, not Integer.")

    print(f"~ Details ~\n\nHost IP: {HOST}\nHost Port: {PORT}\n")
     
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
        # Format for adding new commands: <command-name>: (func, "help message", "name-to-be-shown-at-help-message")
        # If None is entered in the help message, it is considered private, and will not be shown in the help command.

        self.command_list = {
            "status": (lambda *a: self.status(*a), "A debug message, good to see if your connected to host.", "status"), 
            "clone": (lambda *a: self.download_repo(*a), "Clone git repo. (clone <git-link> <name-of-folder-you-want-the-repo-in>)", "clone"),
            "sys": (lambda *a: self.terminal_command(*a), "Execute a terminal / cmd command. (sys <terminal-cmd> <args-for-cmd>)", "sys"),
            "rm": (lambda *a: self.remove_repo(*a), "Removes a repo from scripts folder. (rm <name-you-entered-for-repo>)", 'rm'),
            "run": (lambda *a: self._execute_repo_thread(*a), "Executes a python file, you must know the script path to run. (run <path-to-script>) Example: run RemoteExecutor/src/client.py", 'run'),
            "!": (lambda *a: self._disconnect_client_gracefully(*a), None, 'internal command'),
            "help": (lambda *a: self.send_help(*a), "This command.", 'help'),
            "terminate": (lambda *a: self.terminate_executing_script(*a), "Terminates a script that is running.", "terminate"),
            "repos": (lambda *a: self.show_repos(*a), "Shows all repos downloaded.", 'repos'),
            "pkg": (lambda *a: self.package_manager(*a), "Downloads package for specified repo.", "pkg")
        }
        self.finished = False
        self.proc = None
        super().__init__(*args, **kwargs)

    def send_message(self, message: str, with_newline=True, raw=False):
        msg = Message(str(f"{nl if with_newline else ''}{message}"), None, self.host)
        self.client.sendall(pickle.dumps(msg) if not raw else message.encode())

    def wait_for_input(self, keyword: str) -> list[bool, str]:
        input = self.client.recv(1024).decode()
        return [True, input] if str(input) == str(keyword) else [False, input]

    # Server Commands

    def package_manager(self, *args):
        m = errors[1]
        try:
            sub_command = args[0]
            package = args[1]
            repo = args[2]
            if not os.path.exists(f"src/dependencies/{repo}") and sub_command == "install":
                os.mkdir(f"src/dependencies/{repo}")
            
            if sub_command == "install":
                os.mkdir(f"src/dependencies/{repo}/{package}")
                self.terminal_command(*(f"source bin/activate && pip install -t src/dependencies/{repo}/{package} {package}",), quiet=True, absolute=True)
                m = f"Installed {package}"
            elif sub_command == "uninstall":
                shutil.rmtree(f"src/dependencies/{repo}/{package}")
                m = f"Removed {package}."
            else:
                pass
        except IndexError:
            m = errors[0]
        finally:
            self.send_message(m)

    def show_repos(self, *args):
        self.send_message('\n'.join([r for r in os.listdir("src/scripts") if os.path.isdir(f"src/scripts/{r}")])+"\n..")

    def terminate_executing_script(self, *a):
        if self.proc:
            self.proc.kill()
            self.send_message("Terminated the script.")
        else:
            self.send_message("No script running.")

    def send_help(self, *args):
        help_msg = ""
        for cmd in list(self.command_list.values()):
            if cmd[1]:
                help_msg += f"{cmd[2]} - {cmd[1]}\n"

        self.send_message(help_msg)
    
    def _execute_repo_thread(self, *a):
        Thread(target=self.run_repo, args=(*a,)).start()

    def run_repo(self, *args):
        command = "python3"
        m = errors[1]

        try:
            if not args[0]:
                raise IndexError()

            host_folder = args[0].split("/")
            sargs = ' '.join([command]+['/'.join(host_folder[1:])]+list(args[1:]))
            
            if len(sargs) <= 7:
                m = f"You cannot provide just the repo name, you also need an entry point (Example: {host_folder[0]}/main.py, not just {host_folder[0]})"
            else:
                print(sargs, host_folder, args)
                self.proc = subprocess.Popen(sargs, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=f"src/scripts/{host_folder[0]}")
                
                while self.proc.poll() is None:
                    for line in self.proc.stdout:
                        time.sleep(0.025)
                        self.send_message(line.decode(), False)

                    for error in self.proc.stderr:
                        time.sleep(0.025)
                        self.send_message(error.decode(), False)
                else:
                    m = "Finished Executing."

        except IndexError:
            m = errors[0]
        except FileNotFoundError:
            m = errors[2]
        finally:
            self.proc = None
            self.send_message(m)

    def remove_repo(self, *args):
        try:
            repo = args[0]
            m = f'Removed the repo "{repo}"'
            shutil.rmtree(f"src/scripts/{repo}")
        except IndexError:
            m = errors[0]
        except OSError:
            m = errors[2]
        finally:
            self.send_message(m)

    def terminal_command(self, *args, quiet=False, absolute=False):
        m = errors[1]
        print(args)
        try:
            if args[0] in allowed_commands or absolute:
                m = os.popen(' '.join(args)).read()
            else:
                m = "Command does not exist or is not allowed."
        except IndexError:
            m = errors[0]
        finally:
            if not quiet:
                self.send_message(m)

    def _disconnect_client_gracefully(self, *args):
        print(f"{self.client.getpeername()} has disconnected.")

        self.client.close()
        self.client = None

    def download_repo(self, *args):
        m = errors[1]
        try:
            repo = args[0]
            saved_as = args[1]
        
            if os.path.exists(f"src/scripts/{saved_as}"):
                m = "Repo with that folder name already exists."
            else:
                self.send_message(f'Attempting to download "{repo}"..')
                os.mkdir(f"src/scripts/{saved_as}")
                Repo.clone_from(repo, f'src/scripts/{saved_as}')
                m = f'Finished downloading "{repo}".\nTo run, use "run {saved_as}"'
        except IndexError:
            m = errors[0]
        except git.exc.GitCommandError:
            os.rmdir(f"src/scripts/{saved_as}")
            m = errors[2]
        finally:
            self.send_message(m)
            
    def status(self, *args):
        self.send_message("200")

    def bind(self, __address) -> None:
        self.host = __address
        return super().bind(__address)

    def process_client(self, client: socket.socket) -> str:
        client_message = client.recv(1024).decode('utf-8').split(' ')
        command = client_message[0]
        args = client_message[1:]
        self.command_list[command][0](*args) if command in self.command_list else "This command does not exist."
        
    def start(self) -> None:
        def next_client():
            self.client.close()
            self.client = None
            
        while True:
            try:
                self.client, addr = super().accept()
                print(f"Connection from {addr[0]}")

                client_version = self.wait_for_input(config_object['VERSION'])

                if not client_version[0]:
                    self.send_message("Incorrect client version.", raw=True)
                    next_client(); continue
                self.send_message("True", raw=True)

                client_password = self.wait_for_input(config_object['PASSWORD'])
                if not client_password[0]:
                    self.send_message("Incorrect Password.", raw=True)
                    next_client(); continue
                self.send_message("True", raw=True)

                self.client_info = {'ver': client_version[1], 'password': client_password[1]}
                time.sleep(0.01)

                self.send_message(f"{config_object['WELCOME_MSG']}\n\n{config_object['NAME']} - Client Version: {self.client_info['ver']} Server Version: {config_object['VERSION']} - {__AUTHOR__}")
                while self.client:
                    self.process_client(client=self.client)
                              
            except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
                print(f"{addr[0]} Disconnected Forcefully.")
                self.client = None
            except AttributeError:
                sys.exit(0)
if __name__ == "__main__":
    main()

        

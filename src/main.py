import socket, sys, pickle, os, shutil, subprocess, time, git, config, json
from classes.message import *

from git import Repo
from threading import Thread, ThreadError
from sysconfig import get_paths

REPO_LOCATION = "src/scripts"
DEP_LOCATION = "src/dependencies" # Not Johnny Depp
SITE_PACKAGES = get_paths()["purelib"]
CURRENT_DIRECTORY = os.getcwd()

config_object = config.Config("src/host-sources/host-config.cfg")
os.system("clear")
# Don't use this code if you do not like having risks. This script uses Pickle to send class objects.
# Use at your own risk. (Similar risks to using eval() or exec())

# I do not bother to use asyncio. This is meant for one connection at a time.

# Commonly used errors

try:
    HOST, PORT = sys.argv[1:]
    PORT = int(PORT)
except ValueError:
    print("Port is a String, not Integer."); exit(1)
    
errors = {
    0: "Missing Arguments.",
    1: "Unknown Error.",
    2: "No repo with that name."
}
os_errors = {
    17: "Package already exists."
}
# Commands allowed in "sys" command
allowed_commands = [
                "ls",
                "ifconfig",
                "pwd",
                "rm",
                "mkdir",
                "cat",
                "echo",
                "touch",
                "mv",
                "git"
]

__AUTHOR__ = "Navid Rohim"

nl = "\n"

"""Removes a path and it's sub-directories, can take multiple paths. (Uses shutil.rmtree and it's arguments)"""
def remove_many(paths: list, *args, **kwargs):
    for path in paths:
        shutil.rmtree(path, *args, **kwargs)

def main():
    try:
        with RemoteExecutor(socket.AF_INET, socket.SOCK_STREAM) as code_host:
            code_host.bind((HOST, PORT))
            code_host.listen(1)

            print(f'~ Details ~\n\nHost IP: {HOST}\nHost Port: {PORT}\nHost listening for incoming connections.')

            code_host.start()
    except ThreadError:
        return print("Cannot bind to port, any lingering connections?")
        
default = {"blacklist": []}
indent_s = 4

def write_blacklist(ip: str=None, clear=False) -> None:
    with open("src/host-sources/blacklist.json", "w") as blacklist_file:
        if clear:
            blacklist_file.write(json.dumps(default, indent=indent_s))
        else:
            try:
                bl_file = get_blacklist()
                bl_file["blacklist"].append(ip)

                blacklist_file.write(json.dumps(bl_file, indent=indent_s))
            except json.decoder.JSONDecodeError:
                write_blacklist(clear=True)

def get_blacklist() -> dict:
    try:
        with open("src/host-sources/blacklist.json", "r") as blacklist_file:
            return json.loads(blacklist_file.read())
    except FileNotFoundError:
        return default
    except json.decoder.JSONDecodeError:
        write_blacklist(clear=True)
        return default

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
            "!": (lambda *a: self._disconnect_client_gracefully(*a), None, 'shutdown signal'),
            "?": (lambda *a: self._update_pulse(*a), None, "heatbeat acknowledgement"),
            "help": (lambda *a: self.send_help(*a), "This command.", 'help'),
            "terminate": (lambda *a: self.terminate_executing_script(*a), "Terminates a script that is running.", "terminate"),
            "repos": (lambda *a: self.show_repos(*a), "Shows all repos downloaded.", 'repos'),
            "pkg": (lambda *a: self.package_manager(*a), "Downloads package for specified repo.", "pkg")
        }
        self.finished = False
        self.proc = self.client = None
        self.bump = True

        super().__init__(*args, **kwargs)

    def send_message(self, message: str, with_newline=True, raw=False):
    
        msg = Message(str(f"{nl if with_newline else ''}{message}"), 0, self.host)
        self.client.sendall(pickle.dumps(msg) if not raw else message.encode())

    # rExe Commands

    def package_manager(self, *args):
        m = None
        
        def _install_package(package: str, repo: str) -> str:
            # TODO: Fix naming scheme for package folders (A-B + _)

            try:
                os.mkdir(f"src/dependencies/{repo}/{package}")
                self.terminal_command(*(f"source bin/activate && pip install -t src/dependencies/{repo}/{package} {package}",), quiet=True, absolute=True)
                return f"Installed {package}"
            except OSError as err:
                return os_errors[int(err.errno)]

        def _uninstall_package(package: str, repo: str) -> str:
            shutil.rmtree(f"src/dependencies/{repo}/{package}")
            return f"Removed {package}."

        def _show_ops():
            return "opts - shows all pkg options\ninstall - Installs a package from PyPi\nuninstall - Removes a package\nshow - Shows all packages installed"

        def _show_repos(repo, _) -> str:
            try:
                return '\n'.join([f"{DEP_LOCATION}/{repo}/{r} (When used in a command: {r})" for r in os.listdir(f"{DEP_LOCATION}/{repo}") if os.path.isdir(f"{DEP_LOCATION}/{repo}/{r}")])
            except FileNotFoundError:
                return errors[2]
        commands = {
            "install": _install_package,
            "uninstall": _uninstall_package,
            "show": _show_repos
        }
        commands_noargs = {
            "opts": _show_ops
        }   
        help = "pkg [install || uninstall || opts] <pip-package || None> <repo || None>"
        try:
            sub_command = args[0].lower()    
            if sub_command in list(commands_noargs):
                m = commands_noargs[sub_command]()
            elif sub_command in list(commands):
                A0, A1 = args[1:]
                m = commands[sub_command](A0, A1)
            else:
                m = f"Unknown option. {help}"

        except (IndexError, ValueError):
            m = f"{errors[0]} {help}"
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
        # TODO: Test if file arguments work

        command = "python3"
        m = errors[1]

        try:
            if not args[0]:
                raise IndexError()

            host_folder = args[0].split("/")
            sargs = ' '.join([command]+['/'.join(host_folder[1:])]+list(args[1:]))
            
            REPO_NAME = host_folder[0]
            _paths = [f"{CURRENT_DIRECTORY}/{DEP_LOCATION}/{REPO_NAME}/{d}" for d in os.listdir(f"src/dependencies/{REPO_NAME}") if os.path.isdir(f"src/dependencies/{REPO_NAME}/{d}")]
            packages = '\n'.join(_paths)

            with open(f"{SITE_PACKAGES}/script_dependencies.pth", "w+") as s_d:
                s_d.write(packages)

            if sargs.strip() == command:
                m = "Enter a valid full path to a python executable."
            else:
                self.proc = subprocess.Popen(sargs, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=f"src/scripts/{REPO_NAME}")
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
            remove_many([f"{REPO_LOCATION}/{repo}", f"{DEP_LOCATION}/{repo}"], ignore_errors=True)

        except IndexError:
            m = errors[0]
        except OSError:
            m = errors[2]
        finally:
            self.send_message(m)

    def terminal_command(self, *args, quiet=False, absolute=False):
        m = errors[1]
        try:
            if args[0] in allowed_commands or absolute:
                m = subprocess.Popen(' '.join(args), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
            else:
                m = "Command does not exist or is not allowed."
        except IndexError:
            m = errors[0]
        finally:
            if not quiet:
                if isinstance(m, tuple):
                    if m[0].decode():
                        m = m[0].decode()
                    else:
                        m = m[1].decode()

                self.send_message(m)

    def _disconnect_client_gracefully(self, *args):

        print(f"Client has disconnected.")
        self.client.close()
        self.client = None 
    
    def _update_pulse(self, *args):
        self.bump = True

    def download_repo(self, *args):
        m = errors[1]
        try:

            repo = args[0]
            saved_as = args[1]
        
            if os.path.exists(f"src/scripts/{saved_as}"):
                m = "Repo with that folder name already exists."
            else:
                try:
                    self.send_message(f'Attempting to download "{repo}"..')
                    os.mkdir(f"{REPO_LOCATION}/{saved_as}")
                    os.mkdir(f"{DEP_LOCATION}/{saved_as}")

                    Repo.clone_from(repo, f'src/scripts/{saved_as}')
                    m = f'Finished downloading "{repo}".'

                except Exception as e:
                    m = f"Could not clone repo, error: {e}"
                    remove_many([f"{REPO_LOCATION}/{saved_as}", f"{DEP_LOCATION}/{saved_as}"])

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

    def process_client(self) -> str:
        
        try:
            if self.client:
                client_message = self.client.recv(1024).decode().split(" ")
                command = client_message[0]
                args = client_message[1:]

                self.command_list[command][0](*args) if command in self.command_list else "This command does not exist."
        except OSError:
            self.client = None

    def start(self) -> None:
        def next_client():
            self.client.close()
            self.client = None
        
        def wait_for_input(keyword: str) -> list[bool, str]:
            input = self.client.recv(1024).decode()
            return [True, input] if str(input) == str(keyword) else [False, input]

        while True:
            try:
                self.client, addr = super().accept()

                def heartbeat():
                    while self.client != None:
                        for _ in range(30):
                            if self.client: time.sleep(1); continue
                            else: break

                        if self.bump == True:
                            self.bump = False; continue
                        
                    print("Ending heartbeat with client.")
                    self.client = None
                        
                print(f"Connection from {addr[0]}:{addr[1]}")

                blacklist = get_blacklist()["blacklist"]
                if addr[0] in blacklist:
                    self.send_message("You are blacklisted. Disconnecting.", raw=True)
                    time.sleep(0.2)
                    self._disconnect_client_gracefully()

                    return

                client_version = wait_for_input(config_object['VERSION'])

                if not client_version[0]:
                    self.send_message("Incorrect client version.", raw=True)
                    next_client(); return
                self.send_message("True", raw=True)

                client_password = wait_for_input(config_object['PASSWORD'])
                if config_object["PASSWORD"] and not client_password[0]:
                    self.send_message("Incorrect Password.", raw=True)
                    next_client(); return
                self.send_message("True", raw=True)

                self.client_info = {'ver': client_version[1], 'password': client_password[1]}
                time.sleep(0.01)

                # Welcome message
                self.send_message(f"{config_object['WELCOME_MSG']}\n\n{config_object['NAME']} - Client Version: {self.client_info['ver']} Server Version: {config_object['VERSION']} - {__AUTHOR__}")
                Thread(target=heartbeat).start()

                while self.client:
                    self.process_client()
            
            except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
                print(f"{addr[0]} Disconnected Forcefully.")
                self.client = None
            except AttributeError:
                sys.exit(0)
            except KeyboardInterrupt:
                if self.client:
                    self._disconnect_client_gracefully()
                sys.exit(0)

if __name__ == "__main__":
    if float(sys.version.split(" ")[0][:1]) < 3.10 and sys.platform == "darwin":
        main()
    else:
        print("Either Python version is too old (3.10 and newer) or you are not running MacOS.")

        

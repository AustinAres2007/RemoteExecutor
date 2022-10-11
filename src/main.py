
import socket, sys, os, shutil, subprocess, time, config, json

from threading import Thread
from sysconfig import get_paths
from typing import Union

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

"""
Major Issue:
STDOUT data is only sent once the script has executed, this is a problem.

FIXED: use "-u" flag when executing the python script within Popen()
TODO: 
    1. Add Ip configuration in host-config.cfg file
    2. Fix file naming when cloning a repo (Only A-Z and Underscores "_")
    3. Git intergration
"""

HEATBEAT_ACK = "heartbeat_ack"
SHUTDOWN_ACK = "shutdown_ack"
TERMINATE_ACK = "\nterminate_msg_ack"

try:
    HOST, PORT = sys.argv[1:]
    PORT = int(PORT)
except ValueError:
    print("Port is a String, not Integer."); exit(1)
    
errors = {
    0: "Missing Arguments.",
    1: "Unknown Error.",
    2: "No repo with that name, or the repo has no dependencies folder.",
    3: "Corrupted module-index.json file."
}
os_errors = {
    8: "Unbindable hostname.",
    17: "Package already exists.",
    48: "Address already binded too, please kill any remaining connections or use a different port.",
    49: "Cannot assign to supplied address. Use the local address of your device.",
    51: "Network is unreachable, got the right local IP?",
    60: "Could not connect."
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
    except OSError as ose:
        return print(os_errors[int(ose.errno)])
        
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

def get_module_file(repo) -> Union[dict, str]:
    try:
        with open(f"{DEP_LOCATION}/{repo}/module-index.json", 'r') as m_index:
            module_index = json.loads(m_index.read())
        return module_index
    except FileNotFoundError:
        return "module-index.json file not found."
    except json.decoder.JSONDecodeError:
        return errors[3]

def write_module_file(repo, keys: list, value: str) -> Union[dict, str]:
    current_module_file = get_module_file(repo)
    if isinstance(current_module_file, dict):
        new_m_index = current_module_file | {k: value for k in keys}

        with open(f"{DEP_LOCATION}/{repo}/module-index.json", "w") as m_index:
            m_index.write(json.dumps(new_m_index, indent=indent_s))
        
        return new_m_index
    return current_module_file

def remove_without_err(path: str) -> None:
    if os.path.exists(path):
        shutil.rmtree(path) if os.path.isdir(path) else os.remove(path)

# TODO: Handle client error handling (Here)

class RemoteExecutor(socket.socket):
    def __str__(self) -> str:
        return f"RemoteExecutor(host={self.host}, port={self.port})"

    def __init__(self, *args, **kwargs):
        # Format for adding new commands: <command-name>: (func, "help message", "name-to-be-shown-at-help-message")
        # If None is entered in the help message, it is considered private / system, and will not be shown in the help command.

        self.command_list = {
            "status": (lambda *a: self.status(*a), "A debug message, good to see if your connected to host.", "status"), 
            "clone": (lambda *a: self.download_repo(*a), "Clone git repo. (clone <git-link> <name-of-folder-you-want-the-repo-in>)", "clone"),
            "sys": (lambda *a: self.terminal_command(*a), "Execute a terminal / cmd command. (sys <terminal-cmd> <args-for-cmd>)", "sys"),
            "rm": (lambda *a: self.remove_repo(*a), "Removes a repo from scripts folder. (rm <name-you-entered-for-repo>)", 'rm'),
            "run": (lambda *a: self._execute_repo_thread(*a), "Executes a python file, you must know the script path to run. (run <path-to-script>) Example: run RemoteExecutor/src/client.py", 'run'),
            SHUTDOWN_ACK: (lambda *a: self._disconnect_client_gracefully(*a), None, 'shutdown signal'),
            HEATBEAT_ACK: (lambda *a: self._update_pulse(*a), None, "heatbeat acknowledgement"),
            "dvcs":(lambda *a: self.dvcs_manager(*a), None, "Git control system for client API"),
            "help": (lambda *a: self.send_help(*a), "This command.", 'help'),
            "terminate": (lambda *a: self.terminate_executing_script(*a), "Terminates a script that is running.", "terminate"),
            "repos": (lambda *a: self.show_repos(*a), "Shows all repos downloaded.", 'repos'),
            "pkg": (lambda *a: self.package_manager(*a), "Downloads package for specified repo.", "pkg")
        }
        self.finished = False
        self.proc = self.client = None
        self.bump = True

        super().__init__(*args, **kwargs)

    def send_message(self, message: str, terminate: bool=False):
        if terminate:
            message += TERMINATE_ACK

        self.client.sendall(message.encode())

    # rExe Commands
    def dvcs_manager(self, *args):
        m = errors[1]
        try:
            subcommand = args[0]

            if subcommand == "set":
                self.client_info["selected_repo"] = args[1]
                m = f'Set selected repo to "{args[1]}"'
        except IndexError:
            m = errors[0]
        finally:
            self.send_message(m, True)

    def package_manager(self, *args):
        m = None
        
        def _install_package(package: str, repo: str) -> str:
            # TODO: Fix naming scheme for package folders (A-B + _)
            full_repo_path = f"{DEP_LOCATION}/{repo}"
            try:
                # wtf is this line, bruh
                os.mkdir(f"{full_repo_path}/TEMP-PKG")
                return_proc: str = self.terminal_command(*(f"source bin/activate && pip install {package} -t {full_repo_path}/TEMP-PKG --dry-run --no-deps",), absolute=True, send_to_client=False) \
                    [0].split('\n')[-2] \
                        .split(" ")[-1] \
                            .split("-")
                
                for i, sect in enumerate(return_proc):
                    if not any(ch.isdigit() for ch in sect):
                        pkg_foldername = '_'.join(return_proc[:i+1])
                        alt_pkg_name = pkg_foldername.replace("_", "-") # Not used yet

                if os.path.exists(f"{full_repo_path}/{pkg_foldername}"):
                    return "Module already exists."

                self.terminal_command(*(f"source bin/activate && pip install {package} -t {full_repo_path}/TEMP-PKG",), absolute=True)

                time.sleep(1)

                os.rename(f"{full_repo_path}/TEMP-PKG", f"{full_repo_path}/{pkg_foldername}")
                write_module_file(repo, [pkg_foldername, alt_pkg_name], pkg_foldername)

                return f"Installed {package} at {full_repo_path}/{pkg_foldername}"

            except FileNotFoundError:
                return f'Repo "{repo}" has no dependency folder, please make one in "{DEP_LOCATION}" with the name of "{repo}"'
            except OSError as err:
                return os_errors[int(err.errno)] if int(err.errno) in os_errors else err
            finally:
                remove_without_err(f"{full_repo_path}/TEMP-PKG")

        def _uninstall_package(package: str, repo: str) -> str:
            module_index = get_module_file(repo)
            redirect_name = module_index.get(package, None)

            if redirect_name:
                remove_without_err(f"{SITE_PACKAGES}/script_dependencies.pth")
                shutil.rmtree(f"{DEP_LOCATION}/{repo}/{redirect_name}")

                return f"Removed {package} from {repo}."
            return "No package with that name."

        def _show_ops():
            return "opts - shows all pkg options\ninstall - Installs a package from PyPi\nuninstall - Removes a package\nshow - Shows all packages installed"

        def _show_repos(repo, _) -> str:    
            try:
                return '\n'.join([f'{DEP_LOCATION}/{repo}/{r} (When used in a command: "{r}" Uninstall Command: "pkg uninstall {r} demo")' for r in os.listdir(f"{DEP_LOCATION}/{repo}") if os.path.isdir(f"{DEP_LOCATION}/{repo}/{r}")])
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
        help = "pkg [install || uninstall || opts] <pip-package || None> <repo || .>\n\n. = None"
        try:
            sub_command = args[0].lower()    
            if sub_command in list(commands_noargs):
                m = commands_noargs[sub_command]()
            elif sub_command in list(commands):
                A0, A1 = args[1:]
                if os.path.exists(f"{DEP_LOCATION}/{A1}"):
                    m = commands[sub_command](A0, A1)
                else:
                    m = errors[2]
            else:
                m = f"Unknown option. {help}"

        except (IndexError, ValueError):
            m = f"{errors[0]} {help}"
        finally:
            self.send_message(m, True)

    def show_repos(self, *args):
        self.send_message('\n'.join([r for r in os.listdir("src/scripts") if os.path.isdir(f"src/scripts/{r}")])+"\n..", True)

    def terminate_executing_script(self, *a):
        m = errors[1]
        if self.proc:
            self.proc.kill()
            m = "Terminated the script."
        else:
            m = "No script running."
        
        self.send_message(m, True)

    def send_help(self, *args):
        help_msg = ""
        for cmd in list(self.command_list.values()):
            if cmd[1]:
                help_msg += f"{cmd[2]} - {cmd[1]}\n"

        self.send_message(help_msg, True)
    
    def _execute_repo_thread(self, *a):
        Thread(target=self.run_repo, args=(*a,)).start()

    def run_repo(self, *args):
        # TODO: Test if file arguments work

        command = "python3 -u" # -u flag is required for stdout to work properly.
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
                self.send_message("\n\n~~~ BEGIN SCRIPT~~~\n\n")
                self.proc = subprocess.Popen(sargs, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=f"src/scripts/{REPO_NAME}")
                while self.proc.poll() is None:

                    for line in self.proc.stdout:
                        time.sleep(0.025)
                        self.send_message(line.decode().strip())
                
                    for error in self.proc.stderr:
                        time.sleep(0.025)
                        self.send_message(error.decode())

                else:
                    m = "Finished Executing."

        except IndexError:
            m = errors[0]
        except FileNotFoundError:
            m = errors[2]
        finally:
            self.proc = None
            self.send_message(m, True)

    def remove_repo(self, *args):
        m = errors[1]
        try:
            repo = args[0]
            m = f'Removed the repo "{repo}"'
            remove_many([f"{REPO_LOCATION}/{repo}", f"{DEP_LOCATION}/{repo}"])

        except IndexError:
            m = errors[0]
        except OSError:
            m = errors[2]
        finally:
            self.send_message(m, True)

    def terminal_command(self, *args, quiet=False, absolute=False, send_to_client=True, path: Union[os.PathLike, None, str]=None) -> tuple[str, Union[tuple[bytes, bytes], int]]:
        m = errors[1]
        m_proc = 1
        try:
            if (args[0] in allowed_commands) or absolute:
                m_proc = subprocess.Popen(' '.join(args), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=path)
                m = m_proc.communicate()
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

                if send_to_client:
                    self.send_message(m, terminate=True)
                return (m, m_proc)

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
            
            if os.path.exists(f"{REPO_LOCATION}/{saved_as}") and os.path.exists(f"{DEP_LOCATION}/{saved_as}"):
                m = "Repo with that folder name already exists."
            else:
                try:
                    self.send_message(f'Attempting to download "{repo}"..')
                    os.mkdir(f"{REPO_LOCATION}/{saved_as}")
                    os.mkdir(f"{DEP_LOCATION}/{saved_as}")

                    with open(f"{DEP_LOCATION}/{saved_as}/module_index.json", 'w+') as module_map:
                        module_map.write(json.dumps({}, indent=indent_s))

                    self.terminal_command(f"git clone {repo} {saved_as}", absolute=True, path=REPO_LOCATION)
                    m = f'Finished downloading "{repo}".'
                except Exception as e:
                    m = f"Could not clone repo, error: {e}"
                    remove_many([f"{REPO_LOCATION}/{saved_as}", f"{DEP_LOCATION}/{saved_as}"])

            m = errors[2]
        except IndexError:
            m = errors[0]
        finally:
            self.send_message(m, True)
            
    def status(self, *args):
        self.send_message("200", True)

    def bind(self, __address) -> None:
        self.host = __address
        return super().bind(__address)

    def process_client(self):
        
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
                        
                print(f"\n\n{'~'*15}\n\nConnection from {addr[0]}:{addr[1]}")

                blacklist = get_blacklist()["blacklist"]
                if addr[0] in blacklist:
                    self.send_message("You are blacklisted. Disconnecting.", raw=True)
                    time.sleep(0.2)
                    self._disconnect_client_gracefully()

                    return

                client_version = wait_for_input(config_object['VERSION'])

                if not client_version[0]:
                    self.send_message("Incorrect client version.")
                    next_client(); return
                self.send_message("True")

                client_password = wait_for_input(config_object['PASSWORD'])
                if config_object["PASSWORD"] and not client_password[0]:
                    self.send_message("Incorrect Password.")
                    next_client(); return

                self.send_message("True")

                self.client_info = {'ver': client_version[1], 'password': client_password[1], 'selected_repo': None}
                time.sleep(0.01)

                # Welcome message
                self.send_message(f"{config_object['WELCOME_MSG']}\n\n{config_object['NAME']} - Client Version: {self.client_info['ver']} Server Version: {config_object['VERSION']} - {__AUTHOR__}", True)
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
    if (float(sys.version.split(" ")[0][:4]) == 3.10 and sys.platform == "darwin" and os.system("git --version && clear") == 0):
        print("Passed requirement check."); main()
    else:
        print(f"""Either Python version is too old (3.10 and newer, you are running {sys.version.split(' ')[0]})
        you are not running Darwin (You are running {sys.platform})
        or Git is not installed.""")


        

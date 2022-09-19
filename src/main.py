import socket, sys, pickle, os, shutil, subprocess, time
from typing import *
from classes.message import *
from git import Repo


# Don't use this code if you do not like having risks. This script uses Pickle to send class objects.
# Use at your own risk. (Similar risks to using eval() or exec())

# I do not bother to use asyncio. This is meant for one connection at a time.
errors = {
    0: "Missing Arguments."
}

def main():

    try:
        HOST, PORT = sys.argv[1:]
        PORT = int(PORT)
    except ValueError:
        return print("Port is a String, not Integer.")

    print(f"~ Details ~\n\nHost IP: {HOST}\nHost Port: {PORT}\n")
    with RemoteExecutor(socket.AF_INET, socket.SOCK_STREAM) as code_host:
        try:
            code_host.bind((HOST, PORT))
            code_host.listen(1)

            print('Host listening for incoming connections.')

            code_host.start()
        except OSError:
            return print("Cannot connect to given port. Try again in about 15 seconds.")

# TODO: Handle client error handling (Here)

class RemoteExecutor(socket.socket):
    def __str__(self) -> str:
        return f"RemoteExecutor(host={self.host}, port={self.port})"

    def __init__(self, *args, **kwargs):
        self.command_list = {
            "status": lambda *a: self.status(*a), 
            "clone": lambda *a: self.download_repo(*a),
            "echo": lambda *a: self.echo_to_client(*a),
            "exit": lambda *a: self.close_connection(*a),
            "sys": lambda *a: self.terminal_command(*a),
            "rm": lambda *a: self.remove_repo(*a),
            "run": lambda *a: self.run_repo(*a)
        }
        self.finished = False
        super().__init__(*args, **kwargs)

    def send_message(self, message: str):
        msg = Message(str(message), None, self.host)
        self.client.sendall(pickle.dumps(msg))

    # Server Commands
    def run_repo(self, *args):
        command = "python3"
        m = "Unknown Error"

        try:
            execute_path = f"src/scripts/{args[0]}"
            sys_argv = args[1:]
            sargs = [command, execute_path]+list(sys_argv)

            proc = subprocess.Popen(' '.join(sargs), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            while proc.poll() is None:
                for line in proc.stdout:
                    time.sleep(0.025)
                    self.send_message(line.decode())

                for error in proc.stderr:
                    time.sleep(0.025)
                    self.send_message(error.decode())
            else:
                m = "Finished Executing."

        except IndexError:
            m = errors[0]
        finally:
            self.send_message(m)

    def remove_repo(self, *args):
        try:
            repo = args[0]
            m = f'Removed the repo "{repo}"'
            shutil.rmtree(f"src/scripts/{repo}")
        except IndexError:
            m = errors[0]
        except OSError:
            m = "Repo does not exist."
        finally:
            self.send_message(m)

    def terminal_command(self, *args):
        m = None
        try:
            allowed_commands = [
                "ls",
                "ifconfig",
                "pwd",
                "pip"
            ]
            if args[0] in allowed_commands:
                command = ' '.join(args)
                m = os.popen(command).read()
            else:
                m = "Command does not exist or is not allowed."
        except IndexError:
            m = errors[0]
        finally:
            self.send_message(m)

    def close_connection(self, *args):
        self.close_connection()
        sys.exit(0)

    def echo_to_client(self, *args):
        self.send_message(' '.join(args))

    def download_repo(self, *args):
        try:
            repo = args[0]
            saved_as = args[1]
        except IndexError:
            return self.send_message(errors[0])

        self.send_message(f'Downloading "{repo}"..')
        os.mkdir(f"src/scripts/{saved_as}")
        Repo.clone_from(repo, f'src/scripts/{saved_as}')

        self.send_message(f'Finished downloading "{repo}".\nTo run, use "run {saved_as}"')

    def status(self, *args):
        self.send_message("200")

    def bind(self, __address) -> None:
        self.host = __address
        return super().bind(__address)

    def process_client(self, client: socket.socket) -> str:
        client_message = client.recv(1024).decode('utf-8').split(' ')
        command = client_message[0]
        args = client_message[1:]
        self.command_list[command](*args) if command in self.command_list else "This command does not exist."
        
    def start(self) -> None:
        while True:
            try:
                self.client, addr = super().accept()
                print(f"Connection from {addr[0]}")
                self.send_message("""You are using this tool with the knowledge that this tool
                    could be unsafe for public use. DO NOT let a person you do not trust use this tool, 
                    as they can access the host computer with terminal or shell commands."""
                )
                while self.client:
                    self.process_client(client=self.client)
                              
            except OSError:
                continue
            except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
                print(f"{addr[0]} Disconnected.")
                self.client = None
            except AttributeError:
                sys.exit(0)
if __name__ == "__main__":
    main()

        

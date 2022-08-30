import socket, os, sys, io
from classes.message import Message, File

# TODO: handle file sending
def error(string):
    return print(string); sys.exit(1)
    
def main():
    try:
        SERVER_HOST: str = sys.argv[1]
        SERVER_PORT: int = int(sys.argv[2])
    except IndexError:
        return error("Not enough parameters in run arguments.")
    except ValueError:
        return error("The port parameter is a string type, not integer.")
    else:
        def close():
            re_client.close()
            return error("Shutting down client.")
            
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as re_client:
            try:
    
                re_client.connect((SERVER_HOST, SERVER_PORT))
                commands = {
                        "exit": lambda: close(),
                        "status": lambda: None,
                        "shutdown": lambda: None,
                        "project": lambda: None
                }
                client_side_only = ['exit']
                
            except (ConnectionRefusedError, ConnectionError):
                return error("Server refused connection / the server does not exist.")
            
            else:
                while True:
                    try:
        
                        command = input(f"Send to {SERVER_HOST}:{SERVER_PORT} >>> ")
        
                    
                        commands[command]()
                        if command not in client_side_only:
                            re_client.sendall(command.encode())
                            reply = re_client.recv(1024).decode('utf-8')
                            print(reply)
        
                    except KeyError:
                        print(f"{command} is not a client command.")
                    except KeyboardInterrupt:
                        return error("Shutting down client.")

if __name__ == "__main__":
    main()

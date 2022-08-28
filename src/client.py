import socket, sys, pickle

SERVER_HOST: str = "192.168.1.115"
SERVER_PORT: int = 2022

# TODO: handle file sending

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as re_client:

        def close():
            re_client.close()
            sys.exit(0)

        re_client.connect((SERVER_HOST, SERVER_PORT))
        commands = {
                "exit": lambda: close()
        }
        client_side_only = ['exit']

        while True:
            command = input(f"Send to {SERVER_HOST}:{SERVER_PORT} >>> ")

            try:
                commands[command]()
                if command not in client_side_only:
                    re_client.sendall(command.encode())
                    print(pickle.loads(re_client.recv(4096)))

            except KeyError:
                print(f"{command} is not a client command.")

if __name__ == "__main__":
    main()

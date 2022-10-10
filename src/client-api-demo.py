from client import *

def get_message(msg):
    print(msg)

IP = "0.0.0.0"
PORT = 2022
PASSWORD = ""

with RemoteExecutorClient(IP, PORT) as client_instance:
    try:
        while True:
            client_instance.send_command(input("Remote Executor > "), get_message, ignore_unknown=True)  
    except RemoteExecutorError as error:
        if error.errno == 3:
            print("Closed.")
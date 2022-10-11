from client import *

def get_message(msg):
    print(msg)

IP = "192.168.1.190"
PORT = 2022
PASSWORD = ""

with RemoteExecutorClient(IP, PORT, PASSWORD, get_message) as client_instance:
    try:
        while True:
            client_instance.send_command(input("Remote Executor > "), ignore_unknown=True)  
    except RemoteExecutorError as error:
        if error.errno == 3:
            print("Closed.")
from client import *

def get_message(msg):
    print(msg)

with RemoteExecutorClient("192.168.1.190", 2023) as client_instance:
    try:
        while True:
            client_instance.send_command(input("Remote Executor > "), get_message, ignore_unknown=True)  
    except RemoteExecutorError as error:
        if error.errno == 3:
            print("Closed.")
import config
from client import *

cfg = config.Config("src/host-sources/client-config.cfg")

if len(cfg.as_dict()) >= 4:
    IP = cfg["IP"]
    PORT = cfg["PORT"]
    PASSWORD = cfg["PASSWORD"]
    OUTPUT_METHOD = cfg["OUTPUT"]

    if OUTPUT_METHOD in ["DEFAULT"]:
        with RemoteExecutorClient(IP, PORT, PASSWORD, globals()[OUTPUT_METHOD]) as client_instance:
            try:
                while True:
                    client_instance.send_command(input("Remote Executor > "), ignore_unknown=True)  
            except RemoteExecutorError as error:
                if error.errno == 3:
                    print("Closed.")


else:
    print("Config Keys Missing")
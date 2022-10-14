import config
from client import *

try:
    cfg = config.Config("src/host-sources/client-config.cfg")
except FileNotFoundError:
    print("Configuration file not found.")
else:
    def interface():
        if len(cfg.as_dict()) >= 4:
            IP = cfg["IP"]
            PORT = cfg["PORT"]
            PASSWORD = cfg["PASSWORD"]
            OUTPUT_METHOD = cfg["OUTPUT"]

            if OUTPUT_METHOD in ["DEFAULT"]:
                try:
                    with RemoteExecutorClient(IP, PORT, PASSWORD, globals()[OUTPUT_METHOD], True, True) as client_instance:
                        while True:
                            client_instance.send_command(input("Remote Executor > "), ignore_unknown=True)  
                except RemoteExecutorError as error:
                    if error.errno == 3:
                        print("Closed."); return


        else:
            print("Config Keys Missing")

    if __name__ == "__main__":
        interface()
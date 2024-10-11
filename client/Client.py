import socket
import selectors
import ClientLib
import threading
import sys
import random
from gui import ClientGUI

class ThreadedClient ():
    def __init__(self, host="127.0.0.1", port=12345):
        if __debug__:
            print("ThreadedClient.__init__", host, port)

        # Network components
        self._host = host
        self._port = port
        self._listening_socket = None
        self._selector = selectors.DefaultSelector()

        self._stop_flag = threading.Event()

        self._module = None
        self._quitted = False

        self.gui = None

    def start_connection(self, host, port):
        addr = (host, port)
        print("starting connection to", addr)

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # sock.setblocking(False)
        sock.connect_ex(addr)

        # key exchange
        public_intP = sock.recv(1024) 
        public_intG = sock.recv(1024) 

        private_key = random.randint(1, 100) 

        public_key = str((int(public_intG)**private_key)%int(public_intP))
        exchanged_key = sock.recv(1024)
        sock.send(public_key.encode('utf-8'))

        symmetric_key = (int(exchanged_key)**private_key)%int(public_intP)

        self._module = ClientLib.Module(sock, addr, symmetric_key)
        self._module.start()

        self.gui = ClientGUI(self._module, self)
        self._module.gui = self.gui
        self.gui.start()      

    def run(self):
        self.start_connection(self._host, self._port)
    
    def stop(self):
        self._stop_flag.set()
        self._module.close()
        self._module.join()
        sys.exit(0)



if __name__ == "__main__":
    client = ThreadedClient("127.0.0.1", 12345)
    client.run()
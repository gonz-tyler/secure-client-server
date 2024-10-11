import socket
import selectors
import ServerLib
import random

class ThreadedServer():
    def __init__(self, host="127.0.0.1", port=12345):
        if __debug__:
            print("ThreadedServer.__init__", host, port)

        # Network components
        self._host = host
        self._port = port
        self._listening_socket = None
        self._selector = selectors.DefaultSelector()

        # Processing Components
        self._modules = []

    def _configureServer(self):
        self._listening_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Avoid bind() exception: OSError: [Errno 48] Address already in use
        self._listening_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._listening_socket.bind((self._host, self._port))
        self._listening_socket.listen()

        print("listening on", (self._host, self._port))
        # self._listening_socket.setblocking(False)
        self._selector.register(self._listening_socket, selectors.EVENT_READ, data=None)

    def accept_wrapper(self, sock):
        conn, addr = sock.accept()  # Should be ready to read
        print("accepted connection from", addr)

        try:
            # key exchange
            public_intP = str(random.randint(1, 100))
            public_intG = str(random.randint(1, 100))
            conn.send(public_intP.encode('utf-8'))
            conn.send(public_intG.encode('utf-8'))
            private_key = random.randint(1, 100)

            public_key = str((int(public_intG)**private_key)%int(public_intP))

            # keys exchanged
            conn.send(public_key.encode('utf-8'))
            
            exchanged_key = conn.recv(1024)

            # compute symmetric keys
            symmetric_key = (int(exchanged_key)**private_key)%int(public_intP)

            module = ServerLib.Module(conn, addr, symmetric_key)
            self._modules.append(module)
            module.start()

        except Exception as e:
            sock.close()
            print("exception, closing connection to ", addr)

        
        

    def run(self):
        self._configureServer()

        try:
            while True:
                events = self._selector.select(timeout=None)
                for key, mask in events:
                    if key.data is None:
                        self.accept_wrapper(key.fileobj)
                    else:
                       pass
        except KeyboardInterrupt:
            print("caught keyboard interrupt, exiting")
        finally:
            self._selector.close()


if __name__ == "__main__":
    server = ThreadedServer()
    server.run()
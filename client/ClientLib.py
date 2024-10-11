import selectors
import queue
from threading import Thread, Event
import hashlib

class Module (Thread):
    def __init__(self, sock, addr, symmetric_key):
        Thread.__init__(self)

        self._selector = selectors.DefaultSelector()
        self._sock = sock
        self._addr = addr
        self._incoming_buffer = queue.Queue()
        self._outgoing_buffer = queue.Queue()
      
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        self._selector.register(self._sock, events, data=None)
        self.response_event = Event()

        self._authenticated = False
        self.running = True
        self.gui = None
        self.state = "commands"
        self.file_name = ""
        self.authentication_level = "user"
        self.symmetric_key = symmetric_key

    def encrypt(self, message):
        encrypted_message = ''
        for char in message:
            encrypted_message += chr((ord(char) + self.symmetric_key) % 256)
        return encrypted_message
    
    def decrypt(self, message):
        decrypted_message = ''
        for char in message:
            decrypted_message += chr((ord(char) - self.symmetric_key) % 256)
        return decrypted_message

    def run(self):
        try:
            while self.running:
                events = self._selector.select(timeout=1)
                for key, mask in events:
                    try:
                        if mask & selectors.EVENT_READ:
                            self._read()
                        if mask & selectors.EVENT_WRITE and not self._outgoing_buffer.empty():
                            self._write()
                    except Exception as e:
                        print(f"Exception {e} caused closing")
                        self.close()
                # Check for a socket being monitored to continue.
                if not self._selector.get_map():
                    break
        finally:
            self._selector.close()

    def _read(self):
        try:
            data = self._sock.recv(4096)
            if not data:
                raise RuntimeError("Peer closed.")
            # decrypted_data = self.decrypt(data.decode())
            # self._incoming_buffer.put(decrypted_data)
            self._incoming_buffer.put(data)
            self.response_event.set()  # Signal that new data is available
            
        except BlockingIOError:
            pass
        except Exception as e:
            print(f"Error during reading: {e}")
            self.close()
        if self._authenticated:
            self._process_response()
            
    def _start_file_transfer(self, filename):
        try:
            with open(filename, 'wb') as file:
                done = False
                while not done:
                    data = self._incoming_buffer.get()
                    if not data:
                        raise RuntimeError("Peer closed during file transfer.")
                    if data[-5:] == b"<END>":
                        done = True
                        file.write(data[:-5])  # Write the data without the "<END>"
                    else:
                        file.write(data)

        except Exception as e:
            print(f"Error during file transfer: {e}")
            self.close()

    def _write(self):
        try:
            message = self._outgoing_buffer.get_nowait()
        except:
            message = None

        if message:
            try:
                
                sent = self._sock.send(message.encode())
            except BlockingIOError:
                # Resource temporarily unavailable (errno EWOULDBLOCK)
                pass

    def create_message(self, content):        
        if content.startswith("add"):
            command, username, passwd = content.split(" ")
            password = hashlib.sha256(passwd.encode()).hexdigest()
            content = command + " " + username + " " + password
        encrypted_data = self.encrypt(content)
        encrypted_data = encrypted_data
        self._outgoing_buffer.put(encrypted_data)

    def _process_response(self):
        try:
            message = self._incoming_buffer.get()
            if self.gui.state == "admin":
                self.state = "privilege"
            
            encoded_prefix = b"FILE "
            if message.startswith(encoded_prefix):
                self.state = "download"
                message = message.decode()
                command, self.file_name, file_size = message.split(" ")

            try:
                file = open(self.file_name, "ab")
            except:
                pass

            if self.state == "download":
                if message[-5:] == b"<END>":
                    file.write(message[:-5]) # Write the data without the "<END>"
                    file.close()
                    self.state = "commands"
                else:
                    file.write(message)
            elif self.state == "privilege":
                message = self.decrypt(message.decode())
                self.gui.list_all_user_privileges(message)
            else:
                message = self.decrypt(message.decode())
                self.gui.handle_response(message)
        except Exception as e:
            print(f"Exception in _process_response: {e}")
            return None
        
    def _process_login_response(self):
        try:
            message = self._incoming_buffer.get()
            decoded_message = message.decode()
            decrypted_message = self.decrypt(decoded_message)
            # self.gui.handle_response(decoded_message)
            self.gui.handle_response(decrypted_message)

            return decrypted_message
        except Exception as e:
            print(f"Exception in _process_login_response: {e}")
            return None

    def close(self):
        print("closing connection to", self._addr)
        self.running = False
        try:
            self._selector.unregister(self._sock)
            self._sock.close()
        except OSError as e:
            pass
        finally:
            # Delete reference to socket object for garbage collection
            self._sock = None

    def login(self, user, password):
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        self.create_message(f"LOGIN {user}:{hashed_password}")
        response = self._process_login_response()
        if response == "USERSUCCESS":
            self._authenticated = True
            return True
        elif response == "ADMINSUCCESS":
            self._authenticated = True
            self.authentication_level = "admin"
            return True
        elif response == "FAILURE":
            return False
        elif response == "DUPLICATE":
            self.gui.show_popup_message("User is already logged in on another client.")
            return False
import selectors
import queue
from threading import Thread
import os

import sqlite3
import hashlib

user_connections = {}

class Module(Thread):
    def __init__(self, sock, addr, symmetric_key):
        Thread.__init__(self)

        self._selector = selectors.DefaultSelector()
        self._sock = sock
        self._addr = addr

        self._incoming_buffer = queue.Queue()
        self._outgoing_buffer = queue.Queue()

        self.running = True

        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        self._selector.register(self._sock, events, data=None)

        self._authenticated = False
        self.public_items = []
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
                events = self._selector.select(timeout=None)
                for key, mask in events:
                    try:
                        if mask & selectors.EVENT_READ:
                            self._read()
                        if mask & selectors.EVENT_WRITE and not self._outgoing_buffer.empty():
                            self._write()
                    except Exception:
                        self.close()
                if not self._selector.get_map():
                    break
        except KeyboardInterrupt:
            print("caught keyboard interrupt, exiting")
        finally:
            self._selector.close()

    def _read(self):
        try:
            data = self._sock.recv(4096)
        except BlockingIOError:
            print("blocked")
            # Resource temporarily unavailable (errno EWOULDBLOCK)
            pass
        else:
            if data:
                self._incoming_buffer.put(self.decrypt(data.decode()))
            else:
                raise RuntimeError("Peer closed.")

        self._process_response()

    def _write(self):
        try:
            message = self._outgoing_buffer.get_nowait()
        except:
            message = None

        if message:
           
            try:
                sent = self._sock.send(message) # .encode()
            except BlockingIOError:
                # Resource temporarily unavailable (errno EWOULDBLOCK)
                pass

    def _create_message(self, content):
        # if isinstance(content, bytes):
        #     encoded = self.encrypt(content)
        # else:
        encoded = self.encrypt(content)
        self._outgoing_buffer.put(encoded.encode())

    def _process_response(self):
        message = self._incoming_buffer.get()
            
        split_result = message.split(" ", 1)

        # split_result is a list with two elements
        first_part = split_result[0]
        second_part = split_result[1] if len(split_result) > 1 else ""
        self._module_processor(first_part, second_part)

    def _module_processor(self, command, message):
        if command == "add":
                username, password = message.split(" ")
                user, passwd = username, hashlib.sha256(password.encode()).hexdigest()
                connection = sqlite3.connect("./server/userdata.db")
                cursor = connection.cursor()

                try:
                    cursor.execute("INSERT INTO userdata (username, password, privilege) VALUES (?, ?, ?)", (user, password, "user"))
                    connection.commit()
                    self._create_message("User created.")
                except Exception as e:
                    self._create_message("Cannot create a user with a username that already exists.")
                cursor.close()
                connection.close()

        # check whether authenticated and if not then handle login and dont allow commands to be sent
        elif self._authenticated == False:
            user, password = message.split(":")
            self._handle_login(user, password)
        else:
            if command == "NOOP":
                self._create_message("OK")
            elif command == "help":
                help_string = """These are the commands:
> ls -f  lists files stored in server
> ls -a  lists all usernames
> ls -o  lists all users currently online
> ls -p  lists all users and their privilege level
> delete  filename.extension deletes file called filename.extension if it exists
> add username password  adds username and password of authorization level user
> remove username  if authorized removes deletes account of 'username'
> userdata  lists all users and their privilege level
> privilege username  if authorized changes privilege level of account 'username'"""
                self._create_message(help_string)
            elif command == "ls":
                users = self.list_all_users()
                if message == "-a":
                    if users:
                        result_string = ""
                        for user in users:
                            result_string += user[0] + '\n'
                        # Remove the trailing newline character, if any
                        result_string = result_string.rstrip('\n')
                        self._create_message(result_string)
                    else:
                        self._create_message("No users exist.")
                elif message == "-o":
                    if users:
                        for users in user_connections:
                            self._create_message(users)
                    else:
                        self._create_message("No users exist.")
                elif message == "-f":
                    response = self.list_files("./server/storage/")
                    self._create_message(response)
                elif message == "-p":
                    response = self.list_all_user_privileges()
                    if response:
                        result_string = ""
                        for user in response:
                            result_string += user[0] + " " + user[1] + '\n'
                        
                        # Remove the trailing newline character, if any
                        result_string = result_string.rstrip('\n')
                        self._create_message(result_string)
            elif command == "download":
                self.send_file(message)

            elif command == "upload":
                pass

            elif command == "delete":
                file_path = self.find_file("./server/storage/", message)
                try:
                    os.remove(file_path)
                    self._create_message(f"The file at {file_path} has been deleted successfully.")
                except FileNotFoundError:
                    self._create_message(f"The file at {file_path} does not exist.")
                except Exception as e:
                    self._create_message(f"An error occurred while deleting the file: {e}")        
            elif command == "add":
                if self.authentication_level == "admin":
                    username, password = message.split(" ")
                    user, passwd = username, hashlib.sha256(password.encode()).hexdigest()
                    connection = sqlite3.connect("./server/userdata.db")
                    cursor = connection.cursor()

                    try:
                        cursor.execute("INSERT INTO userdata (username, password, privilege) VALUES (?, ?, ?)", (user, password, "user"))
                        connection.commit()
                        self._create_message("User created.")
                    except Exception as e:
                        self._create_message("Cannot create a user with a username that already exists.")
                    cursor.close()
                    connection.close()
                else:
                    self._create_message("Unauthorized action.\nOnly users with admin level privilege can perform this action.")
            
            elif command == "remove":
                if self.authentication_level == "admin":
                    username = message
                    try:
                        # Connect to the SQLite database
                        connection = sqlite3.connect("./server/userdata.db")
                        cursor = connection.cursor()

                        user_exists = False
                        users = self.list_all_users()

                        for user in users:
                            if username == user[0]:
                                user_exists = True
                                break

                        if user_exists:
                            # Define the DELETE statement with a WHERE clause
                            delete_query = "DELETE FROM userdata WHERE username = ?"

                            # Execute the DELETE statement with the specified condition
                            cursor.execute(delete_query, (username,))

                            # Commit the changes to the database
                            connection.commit()

                            self._create_message(f"Record with username '{username}' deleted successfully.")
                        else:
                            self._create_message("User does not exist.")

                    except sqlite3.Error as e:
                        self._create_message(f"Error deleting record: {e}")

                    finally:
                        # Close the cursor and connection
                        cursor.close()
                        connection.close()
                else:
                    self._create_message("Unauthorized action.\nOnly users with admin level privilege can perform this action.")

            elif command == "userdata":
                response = self.list_all_user_privileges()

                if response:
                    result_string = ""
                    for user in response:
                        result_string += user[0] + " " + user[1] + '\n'
                    
                    # Remove the trailing newline character, if any
                    result_string = result_string.rstrip('\n')
                    
                    self._create_message(result_string)
                    
            elif command == "privilege":
                if self.authentication_level == "admin":
                    # Assuming 'message' contains the username and new password separated by a space
                    username = message

                    # Connect to the SQLite database
                    connection = sqlite3.connect("./server/userdata.db")
                    cursor = connection.cursor()

                    try:
                        # Check if the user exists before updating
                        cursor.execute("SELECT * FROM userdata WHERE username = ?", (username,))
                        existing_user = cursor.fetchone()
                        privilege = existing_user[2]
                        if privilege == "user":
                            privilege = "admin"
                        else:
                            privilege = "user"

                        if existing_user:
                            # Update the password for the existing user
                            cursor.execute("UPDATE userdata SET privilege = ? WHERE username = ?", (privilege, username))
                            connection.commit()
                            print("User updated.")
                        else:
                            print("User not found.")

                    except Exception as e:
                        print(f"An error occurred: {e}")

                    finally:
                        cursor.close()
                        connection.close()
                else:
                    self._create_message("Unauthorized action.\nAdmin authorisation level needed to change user privilege.")


            else:
                self._create_message("Unknown command.")


    def send_file(self, filename):
        file_path = self.find_file("./server/storage/", filename)
        if file_path:
            print("file found")
            file_size = os.path.getsize(file_path)

            # self._create_message(f"FILE {filename} {file_size}")
            stringw = f"FILE {filename} {file_size}"
            self._outgoing_buffer.put(stringw.encode())

            with open(file_path, "rb") as f:
                print("file open")
                chunk_size = 4096
                while True:
                    data_chunk = f.read(chunk_size)
                    # print(f"data chunk {data_chunk}")
                    if not data_chunk:
                        break
                    # self._create_message(data_chunk)
                    self._outgoing_buffer.put(data_chunk) #remove encode
                    # print("chunk sent")
            # self._create_message("<END>")
            self._outgoing_buffer.put(b"<END>")
            print("file end")
        else:
            self._create_message(f"File {filename} not found.")

            # self._create_message("downloading")


    def find_file(self, folder, target_file):
        for root, dirs, files in os.walk(folder):
            for file in files:
                if file == target_file:
                    return os.path.join(root, file)

            for subdir in dirs:
                subdir_path = os.path.join(root, subdir)
                result = self.find_file(subdir_path, target_file)
                if result:
                    return result
                
        return None  # Return None if the target file is not found in the entire directory tree

    def list_all_users(self):
        # Connect to the SQLite database
        connection = sqlite3.connect("./server/userdata.db")
        # Create a cursor object to interact with the database
        cursor = connection.cursor()
        # Execute a SELECT query to retrieve all usernames from the 'users' table
        cursor.execute("SELECT username FROM userdata")
        # Fetch all the results
        users = cursor.fetchall()
        # Close the cursor and connection
        cursor.close()
        connection.close()

        return users
    
    def list_all_user_privileges(self):
        # Connect to the SQLite database
        connection = sqlite3.connect("./server/userdata.db")
        # Create a cursor object to interact with the database
        cursor = connection.cursor()
        # Execute a SELECT query to retrieve all usernames from the 'users' table
        cursor.execute("SELECT username, privilege FROM userdata")
        # Fetch all the results
        user_privileges = cursor.fetchall()
        # Close the cursor and connection
        cursor.close()
        connection.close()

        return user_privileges
    
    def list_files(self, folder, indent=0):
        entries = []

        current_indent = '  ' * indent
        entries.append(f"{current_indent}- {os.path.basename(folder)}/\n")

        # Separate directories and files
        subdirectories = []
        files = []

        for entry in os.listdir(folder):
            entry_path = os.path.join(folder, entry)
            if os.path.isdir(entry_path):
                subdirectories.append(entry)
            elif os.path.isfile(entry_path):
                files.append(entry)

        # Display subdirectories
        for subdir in subdirectories:
            subdir_path = os.path.join(folder, subdir)
            entries.append(self.list_files(subdir_path, indent + 1))

        # Display files
        for file in files:
            entries.append(f"{current_indent}  - {file}\n")

        result = "".join(entries)
        return result
    
    
    def _handle_login(self, user, password):
        if not user in user_connections.keys():
            if self._authenticate_user(user, password):
                connection = sqlite3.connect("./server/userdata.db")
                cursor = connection.cursor()
                cursor.execute("SELECT username FROM userdata WHERE privilege ='admin'")
                admin_users = cursor.fetchall()
                cursor.close()
                connection.close()
                found = any(user == user_tuple[0] for user_tuple in admin_users)
                if found:
                    self._create_message("ADMINSUCCESS")
                    self.authentication_level = "admin"
                else:
                    self._create_message("USERSUCCESS")
                self._authenticated = True
                # self.set_online_status(True, user)

                user_connections[user] = self
            else:
                self._create_message("FAILURE")
        else:
            self._create_message("DUPLICATE")

    def _authenticate_user(self, user, password):
        conn = sqlite3.connect("./server/userdata.db")
        cur = conn.cursor()

        cur.execute("SELECT* FROM userdata WHERE username = ? AND password = ?", (user, password))

        if cur.fetchall():
            return True
        else:
            return False
        
    def _get_user_for_session(self):
        # Iterate through user_connections to find the username associated with this connection
        for username, module_instance in user_connections.items():
            if module_instance == self:
                return username
        return None


    def close(self):
        print("closing connection to", self._addr)
        # Set the user associated with this session token to offline
        user = self._get_user_for_session()
        if user:
            del user_connections[user]

        self.running = False
        try:
            self._selector.unregister(self._sock)
            self._sock.close()
        except OSError as e:
            print(
                f"error: socket.close() exception for",
                f"{self._addr}: {repr(e)}",
            )
        finally:
            # Delete reference to socket object for garbage collection
            self._sock = None


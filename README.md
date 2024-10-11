# Server-Client Command Line Application

This project consists of a **Server** and **Client** application that allow user authentication and file management via command line commands. You can create accounts, list users, manage files, and execute commands with different authorization levels.

## Prerequisites
- Python 3.x installed on your system.

## Running the Project

### Start the Server

- Make sure there is a file called userdata.db in the server directory

- Open a terminal and navigate to the project directory where the `Server.py` script is located:
  ```bash
  cd path/to/server-directory
  python3 Server.py
  ```
  ```bash
  cd path/to/client-directory
  python3 Client.py
  ```

### Logging In or Creating an Account
After running the Client, you will be prompted to log in. You can either:

- Input one of the following default credentials:
  - user1, password1
  - user2, password2
  - user3, password3
  - admin, adminpass
- OR, create a new account by following the prompt.

### These are the available Commands

| Command                           | Description                                           |
|-----------------------------------|-------------------------------------------------------|
| `ls -f`                           | Lists all files stored on the server.               |
| `ls -a`                           | Lists all registered usernames.                       |
| `ls -o`                           | Lists all users currently online.                    |
| `ls -p`                           | Lists all users and their authorization level.       |
| `delete filename.extension`       | Deletes the file named `filename.extension`.          |
| `add username password`           | Adds a new user with the specified username and password. |
| `remove username`                 | Deletes the account with the specified username.     |
| `userdata`                        | Lists all users and their authorization level.       |
| `privilege username`              | Changes the authorization level of the specified username. |
| `clear`                           | Clears the output text box.                          |
| `download filename.extension`     | Downloads the file named `filename.extension`.       |


## Authorization Levels
Different commands require different levels of authorization. The default accounts have the following levels:

- **admin**: Full access, can manage user privileges and delete accounts.
- **user**: Standard access, can list files, add files, etc.

## Example Usage
### Logging In
```bash
> user1
> password1
```
### Listing All Files
```bash
> ls -f
```
Adding a New User (Admin Only)
```bash
> add newuser newpassword
```
Deleting a File
```bash
> delete document.txt
```
Downloading a File
```bash
> download report.pdf
```
### Notes
The file download command transfers data without encryption, so use it with caution.
Ensure you have the necessary authorization level before trying to execute privileged commands.


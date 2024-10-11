import os

def list_files(folder, indent=0):
    current_indent = '    ' * indent
    print(f"{current_indent}- {os.path.basename(folder)}/")

    # Display files
    for file in os.listdir(folder):
        file_path = os.path.join(folder, file)
        if os.path.isfile(file_path):
            print(f"{current_indent}    - {file}")

    # Display subdirectories
    for subdir in os.listdir(folder):
        subdir_path = os.path.join(folder, subdir)
        if os.path.isdir(subdir_path):
            list_files(subdir_path, indent + 1)

# Example: List files in the current directory and its subfolders
folder_path = './server/'  # Replace this with the path of the folder you want to list
list_files(folder_path)
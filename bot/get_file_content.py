def get_file_content(file_name: str):
    with open(file_name, "r") as file:
        return file.read()
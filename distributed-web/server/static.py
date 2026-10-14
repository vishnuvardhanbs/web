import os

mime_types = {
    ".html": "text/html",
    ".css": "text/css",
    ".js": "application/javascript",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".txt": "text/plain"
}


def get_file(path, base_dir):

    if path == "/":
        path = "/index.html"

    file_path = os.path.join(
        base_dir,
        path.lstrip("/")
    )

    if not os.path.isfile(file_path):
        return None, None

    with open(file_path, "rb") as file:
        content = file.read()

    extension = os.path.splitext(file_path)[1].lower()

    content_type = mime_types.get(
        extension,
        "application/octet-stream"
    )

    return content, content_type
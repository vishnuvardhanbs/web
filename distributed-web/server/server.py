import socket
import threading
import json as json_module
import time
import sys

from http import parse_request, create_response
from static import get_file


def register_server(name, domain, port):

    connection = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    connection.connect(
        ("127.0.0.1", 9000)
    )

    message = {
        "type": "register",
        "server": {
            "name": name,
            "domain": domain,
            "host": "127.0.0.1",
            "port": port
        }
    }

    data = json_module.dumps(message).encode()

    connection.sendall(data)
    connection.close()


def unregister_server(name):

    connection = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    connection.connect(
        ("127.0.0.1", 9000)
    )

    message = {
        "type": "unregister",
        "name": name
    }

    data = json_module.dumps(message).encode()

    connection.sendall(data)
    connection.close()


def send_heartbeat(name):

    while True:

        try:

            connection = socket.socket(
                socket.AF_INET,
                socket.SOCK_STREAM
            )

            connection.connect(
                ("127.0.0.1", 9000)
            )

            message = {
                "type": "heartbeat",
                "name": name
            }

            data = json_module.dumps(message).encode()

            connection.sendall(data)
            connection.close()

            time.sleep(3)

        except Exception as e:

            print("heartbeat failed:", e)
            time.sleep(3)


def receive_http_request(connection):

    data = b""

    while b"\r\n\r\n" not in data:

        chunk = connection.recv(4096)

        if not chunk:
            break

        data += chunk

    return data


def handle_client(connection, address):

    print("client connected", address)
    print("Thread:", threading.current_thread().name)

    request = receive_http_request(connection)

    if not request:

        connection.close()
        return

    method, path, version = parse_request(request)

    print("Method:", method)
    print("Path:", path)
    print("Version:", version)

    if method != "GET":

        response = create_response(
            "405 Method Not Allowed",
            "text/html",
            b"<h1>405 Method Not Allowed</h1>"
        )

        connection.sendall(response)
        connection.close()
        return

    content, content_type = get_file(
        path,
        static_directory
    )

    if content is None:

        response = create_response(
            "404 Not Found",
            "text/html",
            b"<h1>404 Not Found</h1>"
        )

    else:

        response = create_response(
            "200 OK",
            content_type,
            content
        )

    connection.sendall(response)
    connection.close()


if len(sys.argv) != 4:

    print(
        "Usage: python3 server.py <port> <domain> <static_directory>"
    )

    sys.exit(1)


port = int(sys.argv[1])
domain = sys.argv[2]
static_directory = sys.argv[3]

name = f"server-{port}"

register_server(
    name,
    domain,
    port
)

heartbeat_thread = threading.Thread(
    target=send_heartbeat,
    args=(name,),
    daemon=True
)

heartbeat_thread.start()

server = socket.socket(
    socket.AF_INET,
    socket.SOCK_STREAM
)

server.setsockopt(
    socket.SOL_SOCKET,
    socket.SO_REUSEADDR,
    1
)

server.bind(
    ("127.0.0.1", port)
)

server.listen()

print(
    f"server is listening at 127.0.0.1:{port}"
)

print(
    f"domain: {domain}"
)

print(
    f"static directory: {static_directory}"
)

try:

    while True:

        connection, address = server.accept()

        thread = threading.Thread(
            target=handle_client,
            args=(connection, address)
        )

        thread.start()

except KeyboardInterrupt:

    print("Server shutting down...")

    unregister_server(name)

    server.close()

    print("Server unregistered.")
import socket
import json
import threading
import time
import sys


def receive_http_request(connection):

    data = b""

    while b"\r\n\r\n" not in data:

        chunk = connection.recv(4096)

        if not chunk:
            break

        data += chunk

    return data


def receive_http_response(connection):

    data = b""

    while b"\r\n\r\n" not in data:

        chunk = connection.recv(4096)

        if not chunk:
            break

        data += chunk

    if b"\r\n\r\n" not in data:
        return data

    header_data, body = data.split(
        b"\r\n\r\n",
        1
    )

    headers = header_data.decode()

    content_length = 0

    for line in headers.split("\r\n"):

        if line.lower().startswith("content-length:"):

            content_length = int(
                line.split(":", 1)[1].strip()
            )

            break

    remaining = content_length - len(body)

    while remaining > 0:

        chunk = connection.recv(
            min(4096, remaining)
        )

        if not chunk:
            break

        body += chunk
        remaining -= len(chunk)

    return header_data + b"\r\n\r\n" + body


def get_servers(name):

    connection = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    connection.connect(
        ("127.0.0.1", 9000)
    )

    message = {
        "type": "list_servers_for_lb",
        "name": name
    }

    data = json.dumps(message).encode()

    connection.sendall(data)

    response = connection.recv(4096)

    connection.close()

    result = json.loads(
        response.decode()
    )

    return result["servers"]


def register_load_balancer(name, domain, port):

    connection = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    connection.connect(
        ("127.0.0.1", 9000)
    )

    message = {
        "type": "register_lb",
        "load_balancer": {
            "name": name,
            "domain": domain,
            "host": "127.0.0.1",
            "port": port
        }
    }

    data = json.dumps(message).encode()

    connection.sendall(data)

    connection.close()


def unregister_load_balancer(name):

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

    data = json.dumps(message).encode()

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

            data = json.dumps(message).encode()

            connection.sendall(data)

            connection.close()

            time.sleep(3)

        except Exception as e:

            print(
                "heartbeat failed:",
                e
            )

            time.sleep(3)


current_server = 0


def forward_request(request, server):

    connection = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    connection.settimeout(3)

    connection.connect(
        (
            server["host"],
            server["port"]
        )
    )

    connection.sendall(request)

    response = receive_http_response(
        connection
    )

    connection.close()

    return response


def handle_client(connection, address):

    global current_server

    print(
        "Client connected:",
        address
    )

    request = receive_http_request(
        connection
    )

    if not request:

        connection.close()

        return

    servers = get_servers(name)

    if not servers:

        response = (
            b"HTTP/1.1 503 Service Unavailable\r\n"
            b"Content-Type: text/html\r\n"
            b"Connection: close\r\n"
            b"\r\n"
            b"<h1>503 Service Unavailable</h1>"
        )

        connection.sendall(
            response
        )

        connection.close()

        return

    start_index = (
        current_server % len(servers)
    )

    for i in range(len(servers)):

        index = (
            start_index + i
        ) % len(servers)

        server = servers[index]

        print(
            "Trying:",
            server["name"]
        )

        try:

            response = forward_request(
                request,
                server
            )

            print(
                "Success:",
                server["name"]
            )

            current_server = index + 1

            connection.sendall(
                response
            )

            connection.close()

            return

        except Exception as e:

            print(
                "Server failed:",
                server["name"],
                e
            )

    response = (
        b"HTTP/1.1 503 Service Unavailable\r\n"
        b"Content-Type: text/html\r\n"
        b"Connection: close\r\n"
        b"\r\n"
        b"<h1>All servers unavailable</h1>"
    )

    connection.sendall(
        response
    )

    connection.close()


if len(sys.argv) != 3:

    print(
        "Usage: python3 load_balancer.py <port> <domain>"
    )

    sys.exit(1)


port = int(sys.argv[1])
domain = sys.argv[2]

name = f"lb-{port}"


register_load_balancer(
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


load_balancer = socket.socket(
    socket.AF_INET,
    socket.SOCK_STREAM
)

load_balancer.setsockopt(
    socket.SOL_SOCKET,
    socket.SO_REUSEADDR,
    1
)

load_balancer.bind(
    ("127.0.0.1", port)
)

load_balancer.listen()

print(
    f"Load balancer listening on 127.0.0.1:{port}"
)

print(
    f"Domain: {domain}"
)


try:

    while True:

        connection, address = (
            load_balancer.accept()
        )

        thread = threading.Thread(
            target=handle_client,
            args=(connection, address)
        )

        thread.start()

except KeyboardInterrupt:

    print(
        "Load balancer shutting down..."
    )

    unregister_load_balancer(
        name
    )

    load_balancer.close()

    print(
        "Load balancer unregistered."
    )
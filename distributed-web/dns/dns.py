import json
import socket


def get_load_balancer(domain):

    connection = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    connection.connect(
        ("127.0.0.1", 9000)
    )

    message = {
        "type": "resolve_domain",
        "domain": domain
    }

    data = json.dumps(message).encode()

    connection.sendall(data)

    response = connection.recv(4096)

    connection.close()

    return json.loads(
        response.decode()
    )


dns_server = socket.socket(
    socket.AF_INET,
    socket.SOCK_DGRAM
)

dns_server.bind(
    ("127.0.0.1", 9025)
)

print(
    "DNS server is listening on 127.0.0.1:9025"
)


while True:

    data, address = dns_server.recvfrom(4096)

    message = json.loads(
        data.decode()
    )

    print(
        "DNS query:",
        message
    )

    domain = message["domain"]

    result = get_load_balancer(
        domain
    )

    if result.get("found"):

        response = {
            "type": "response",
            "domain": domain,
            "host": result["host"],
            "port": result["port"]
        }

    else:

        response = {
            "type": "response",
            "domain": domain,
            "error": "DOMAIN NOT FOUND"
        }

    data = json.dumps(
        response
    ).encode()

    dns_server.sendto(
        data,
        address
    )
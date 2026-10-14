import socket
import threading
import json
import time

servers = {}
load_balancers = {}
lock = threading.Lock()


def redistribute_servers():

    for server in servers.values():

        domain = server.get("domain")

        assigned_lb = None

        for name, load_balancer in load_balancers.items():

            if load_balancer.get("domain") == domain:

                assigned_lb = name
                break

        old_lb = server.get("load_balancer")

        server["load_balancer"] = assigned_lb

        if old_lb != assigned_lb:

            if assigned_lb is not None:

                print(
                    "Assigned",
                    server["name"],
                    "to",
                    assigned_lb
                )

            else:

                print(
                    "No load balancer for",
                    server["name"],
                    "domain:",
                    domain
                )

    print("Current server distribution:")

    for name in load_balancers:

        assigned = []

        for server in servers.values():

            if server.get("load_balancer") == name:

                assigned.append(
                    server["name"]
                )

        print(
            name,
            "->",
            assigned
        )


def resolve_domain(domain):

    for load_balancer in load_balancers.values():

        if load_balancer.get("domain") == domain:

            return {
                "found": True,
                "domain": domain,
                "host": load_balancer["host"],
                "port": load_balancer["port"],
                "load_balancer": load_balancer["name"]
            }

    return {
        "found": False
    }


def health_checker():

    while True:

        current_time = time.time()

        with lock:

            dead_servers = []

            for name, server in list(
                servers.items()
            ):

                if current_time - server["last_seen"] > 10:

                    dead_servers.append(name)

            for name in dead_servers:

                print(
                    "server time out:",
                    name
                )

                del servers[name]

            dead_load_balancers = []

            for name, load_balancer in list(
                load_balancers.items()
            ):

                if current_time - load_balancer["last_seen"] > 10:

                    dead_load_balancers.append(name)

            for name in dead_load_balancers:

                print(
                    "load balancer time out:",
                    name
                )

                del load_balancers[name]

            if dead_servers or dead_load_balancers:

                redistribute_servers()

        time.sleep(2)


health_thread = threading.Thread(
    target=health_checker,
    daemon=True
)

health_thread.start()


def handle_client(connection, address):

    data = connection.recv(4096)

    if not data:

        connection.close()
        return

    message = json.loads(
        data.decode()
    )

    print(
        "Received:",
        message
    )

    message_type = message["type"]

    with lock:

        if message_type == "register":

            server = message["server"]

            name = server["name"]

            server["last_seen"] = time.time()
            server["load_balancer"] = None

            servers[name] = server

            print(
                "Registered server:",
                name,
                "domain:",
                server.get("domain")
            )

            redistribute_servers()

        elif message_type == "register_lb":

            load_balancer = message["load_balancer"]

            name = load_balancer["name"]

            load_balancer["last_seen"] = time.time()

            load_balancers[name] = load_balancer

            print(
                "Registered load balancer:",
                name,
                "domain:",
                load_balancer.get("domain")
            )

            redistribute_servers()

        elif message_type == "heartbeat":

            name = message["name"]

            if name in servers:

                servers[name]["last_seen"] = time.time()

            elif name in load_balancers:

                load_balancers[name]["last_seen"] = time.time()

        elif message_type == "unregister":

            name = message["name"]

            if name in servers:

                del servers[name]

                print(
                    "Unregistered server:",
                    name
                )

                redistribute_servers()

            elif name in load_balancers:

                del load_balancers[name]

                print(
                    "Unregistered load balancer:",
                    name
                )

                redistribute_servers()

        elif message_type == "list_servers":

            response = {
                "servers": list(
                    servers.values()
                )
            }

            data = json.dumps(
                response
            ).encode()

            connection.sendall(data)

        elif message_type == "list_load_balancers":

            response = {
                "load_balancers": list(
                    load_balancers.values()
                )
            }

            data = json.dumps(
                response
            ).encode()

            connection.sendall(data)

        elif message_type == "list_servers_for_lb":

            name = message["name"]

            assigned_servers = []

            for server in servers.values():

                if server.get("load_balancer") == name:

                    assigned_servers.append(server)

            response = {
                "load_balancer": name,
                "servers": assigned_servers
            }

            data = json.dumps(
                response
            ).encode()

            connection.sendall(data)

        elif message_type == "resolve_domain":

            domain = message["domain"]

            response = resolve_domain(
                domain
            )

            data = json.dumps(
                response
            ).encode()

            connection.sendall(data)

    connection.close()


registry = socket.socket(
    socket.AF_INET,
    socket.SOCK_STREAM
)

registry.setsockopt(
    socket.SOL_SOCKET,
    socket.SO_REUSEADDR,
    1
)

registry.bind(
    ("127.0.0.1", 9000)
)

registry.listen()

print(
    "Registry listening on 127.0.0.1:9000"
)


while True:

    connection, address = registry.accept()

    thread = threading.Thread(
        target=handle_client,
        args=(connection, address)
    )

    thread.start()
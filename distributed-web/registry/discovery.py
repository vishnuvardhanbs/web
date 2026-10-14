import socket
import json

connection=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
connection.connect(("127.0.0.1",9000))
message={
    "type":"list"
}
data=json.dumps(message).encode()
connection.sendall(data)
response=connection.recv(4096)
servers = json.loads(response.decode())

print("RAW RESPONSE:")
print(servers)

print("Available servers:")

for server in servers["servers"]:
    print(
        server["name"],
        "→",
        f'{server["host"]}:{server["port"]}'
    )

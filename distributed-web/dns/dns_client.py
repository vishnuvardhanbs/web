import socket
import json

dns_client = socket.socket(
    socket.AF_INET,
    socket.SOCK_DGRAM
)

message = {
    "type": "query",
    "domain": "web.local"
}

data = json.dumps(message).encode()

dns_client.sendto(
    data,
    ("127.0.0.1", 8005)
)

response, address = dns_client.recvfrom(4096)

result = json.loads(response.decode())

print("DNS response:")
print(result)

dns_client.close()
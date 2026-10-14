def parse_request(request):
    request_text=request.decode("utf-8",errors="replace")
    lines=request_text.splitlines()
    request_line=lines[0]
    method,path,version=request_line.split()
    return method,path,version

def create_response(status, content_type, body):

    response = (
        f"HTTP/1.1 {status}\r\n"
        f"Content-Type: {content_type}\r\n"
        f"Content-Length: {len(body)}\r\n"
        f"Connection: close\r\n"
        f"\r\n"
    ).encode()

    return response + body
def receive_http_request(connection):

    data = b""

    while b"\r\n\r\n" not in data:

        chunk = connection.recv(4096)

        if not chunk:
            break

        data += chunk

    return data
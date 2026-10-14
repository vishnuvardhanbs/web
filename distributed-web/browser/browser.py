import socket
import json
import tkinter as tk
from bs4 import BeautifulSoup


# -----------------------------
# DNS
# -----------------------------

def resolve(domain):

    dns_client = socket.socket(
        socket.AF_INET,
        socket.SOCK_DGRAM
    )

    message = {
        "type": "query",
        "domain": domain
    }

    dns_client.sendto(
        json.dumps(message).encode(),
        ("127.0.0.1", 9025)
    )

    response, _ = dns_client.recvfrom(4096)

    result = json.loads(
        response.decode()
    )

    dns_client.close()

    if "error" in result:

        print(
            "DNS error:",
            result["error"]
        )

        return None

    return result["host"], result["port"]


# -----------------------------
# HTTP request
# -----------------------------

def request(host, port, domain, path):

    connection = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    connection.connect(
        (host, port)
    )

    http_request = (
        f"GET {path} HTTP/1.1\r\n"
        f"Host: {domain}\r\n"
        f"Connection: close\r\n"
        f"\r\n"
    )

    connection.sendall(
        http_request.encode()
    )

    response = b""

    while True:

        chunk = connection.recv(4096)

        if not chunk:
            break

        response += chunk

    connection.close()

    return response


# -----------------------------
# Extract HTML body
# -----------------------------

def extract_body(response):

    if b"\r\n\r\n" not in response:

        return ""

    header, body = response.split(
        b"\r\n\r\n",
        1
    )

    return body.decode(
        errors="replace"
    )


# -----------------------------
# HTML renderer
# -----------------------------

def render_node(widget, node):

    if isinstance(node, str):

        text = node.strip()

        if text:

            widget.insert(
                tk.END,
                text
            )

        return

    if node.name is None:

        return

    # -------------------------
    # Headings
    # -------------------------

    if node.name in [
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6"
    ]:

        widget.insert(
            tk.END,
            "\n"
        )

        start = widget.index(
            tk.END
        )

        for child in node.children:

            render_node(
                widget,
                child
            )

        end = widget.index(
            tk.END
        )

        size = {
            "h1": 28,
            "h2": 24,
            "h3": 20,
            "h4": 18,
            "h5": 16,
            "h6": 14
        }[node.name]

        widget.tag_add(
            node.name,
            start,
            end
        )

        widget.tag_config(
            node.name,
            font=(
                "Arial",
                size,
                "bold"
            )
        )

        widget.insert(
            tk.END,
            "\n\n"
        )

        return

    # -------------------------
    # Paragraph
    # -------------------------

    if node.name == "p":

        widget.insert(
            tk.END,
            "\n"
        )

        for child in node.children:

            render_node(
                widget,
                child
            )

        widget.insert(
            tk.END,
            "\n\n"
        )

        return

    # -------------------------
    # Line break
    # -------------------------

    if node.name == "br":

        widget.insert(
            tk.END,
            "\n"
        )

        return

    # -------------------------
    # Div
    # -------------------------

    if node.name == "div":

        widget.insert(
            tk.END,
            "\n"
        )

        for child in node.children:

            render_node(
                widget,
                child
            )

        widget.insert(
            tk.END,
            "\n"
        )

        return

    # -------------------------
    # Bold
    # -------------------------

    if node.name in [
        "b",
        "strong"
    ]:

        start = widget.index(
            tk.END
        )

        for child in node.children:

            render_node(
                widget,
                child
            )

        end = widget.index(
            tk.END
        )

        widget.tag_add(
            "bold",
            start,
            end
        )

        return

    # -------------------------
    # Italic
    # -------------------------

    if node.name in [
        "i",
        "em"
    ]:

        start = widget.index(
            tk.END
        )

        for child in node.children:

            render_node(
                widget,
                child
            )

        end = widget.index(
            tk.END
        )

        widget.tag_add(
            "italic",
            start,
            end
        )

        return

    # -------------------------
    # Everything else
    # -------------------------

    for child in node.children:

        render_node(
            widget,
            child
        )


def render_html(widget, html):

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    body = soup.body

    if body:

        for child in body.children:

            render_node(
                widget,
                child
            )

    else:

        for child in soup.children:

            render_node(
                widget,
                child
            )


# ============================================================
# BROWSER WINDOW
# ============================================================

root = tk.Tk()

root.title(
    "Distributed Browser"
)

root.geometry(
    "1000x700"
)


# ============================================================
# ADDRESS BAR
# ============================================================

toolbar = tk.Frame(
    root
)

toolbar.pack(
    fill=tk.X,
    padx=10,
    pady=10
)


url_entry = tk.Entry(
    toolbar,
    font=(
        "Arial",
        14
    )
)

url_entry.pack(
    side=tk.LEFT,
    fill=tk.X,
    expand=True
)


go_button = tk.Button(
    toolbar,
    text="Go",
    font=(
        "Arial",
        12
    )
)

go_button.pack(
    side=tk.RIGHT,
    padx=(10, 0)
)


# ============================================================
# WEB PAGE AREA
# ============================================================

text = tk.Text(
    root,
    wrap=tk.WORD,
    font=(
        "Arial",
        14
    )
)

text.pack(
    fill=tk.BOTH,
    expand=True,
    padx=10,
    pady=(0, 10)
)


# ============================================================
# TEXT STYLES
# ============================================================

text.tag_config(
    "bold",
    font=(
        "Arial",
        14,
        "bold"
    )
)

text.tag_config(
    "italic",
    font=(
        "Arial",
        14,
        "italic"
    )
)


# ============================================================
# LOAD PAGE
# ============================================================

def load_page():

    domain = url_entry.get().strip()

    if not domain:

        return

    print(
        f"Resolving {domain}..."
    )

    # Clear previous page

    text.config(
        state=tk.NORMAL
    )

    text.delete(
        "1.0",
        tk.END
    )

    # DNS resolution

    address = resolve(
        domain
    )

    if address is None:

        text.insert(
            tk.END,
            f"DNS resolution failed for {domain}"
        )

        text.config(
            state=tk.DISABLED
        )

        return

    host, port = address

    print(
        f"{domain} resolved to {host}:{port}"
    )

    try:

        # HTTP request

        response = request(
            host,
            port,
            domain,
            "/"
        )

        # Extract HTML

        html = extract_body(
            response
        )

        print(
            "========== HTML RECEIVED =========="
        )

        print(
            html
        )

        print(
            "==================================="
        )

        # Render HTML

        render_html(
            text,
            html
        )

    except Exception as e:

        print(
            "Browser error:",
            e
        )

        text.insert(
            tk.END,
            "Browser error:\n\n"
            + str(e)
        )

    text.config(
        state=tk.DISABLED
    )


# ============================================================
# EVENTS
# ============================================================

go_button.config(
    command=load_page
)


url_entry.bind(
    "<Return>",
    lambda event: load_page()
)


# ============================================================
# START
# ============================================================

url_entry.focus()

root.mainloop()
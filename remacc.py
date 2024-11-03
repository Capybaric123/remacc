import socket
import threading
import sys

# Server settings
SERVER_IP = '0.0.0.0'  # Listen on all network interfaces for server
SERVER_PORT = 12345
ADDRESS = (SERVER_IP, SERVER_PORT)

# Store channels
channels = {}

def start_server():
    """Start the server to handle multiple clients and channels."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(ADDRESS)
    server.listen(5)
    print(f"[SERVER] Server started at {SERVER_IP}:{SERVER_PORT}")

    def broadcast(message, channel, sender=None):
        """Send a message to all clients in a channel except the sender."""
        for client in channels.get(channel, []):
            if client != sender:
                try:
                    client.send(message.encode())
                except Exception as e:
                    print(f"[ERROR] Could not send message: {e}")

    def handle_client(client_socket, address):
        """Handle communication with a single client."""
        channel = None
        client_socket.send("Welcome to ConsoleChat! Use /channel <name> to join.\n".encode())
        
        try:
            while True:
                msg = client_socket.recv(1024).decode()
                
                # Check for channel join command
                if msg.startswith("/channel"):
                    _, channel_name = msg.split(maxsplit=1)
                    if channel:
                        channels[channel].remove(client_socket)
                    channel = channel_name.strip()
                    if channel not in channels:
                        channels[channel] = []
                    channels[channel].append(client_socket)
                    client_socket.send(f"Joined channel {channel}\n".encode())
                    broadcast(f"[{address}] joined the channel.", channel, client_socket)
                
                # Handle normal chat message
                elif msg:
                    if channel:
                        broadcast(f"[{address}] {msg}", channel, client_socket)
                    else:
                        client_socket.send("Join a channel first. Use /channel <name>.\n".encode())
                
        except (ConnectionResetError, ConnectionAbortedError):
            print(f"[DISCONNECT] {address} disconnected")
        finally:
            if channel:
                channels[channel].remove(client_socket)
            client_socket.close()

    print("[START] Server is running and waiting for connections...")
    while True:
        client_socket, addr = server.accept()
        print(f"[NEW CONNECTION] {addr} connected.")
        client_thread = threading.Thread(target=handle_client, args=(client_socket, addr))
        client_thread.start()


def start_client():
    """Connect to the server as a client and interact in console."""
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect(ADDRESS)
    except ConnectionRefusedError:
        print("[ERROR] Could not connect to the server. Make sure the server is running.")
        return

    def receive_messages():
        """Receive messages from server and display in console."""
        while True:
            try:
                message = client.recv(1024).decode()
                if not message:
                    print("[ERROR] Server closed the connection.")
                    break
                print(message)
            except (ConnectionResetError, ConnectionAbortedError):
                print("[ERROR] Connection closed by the server.")
                break

    # Start a thread to listen for messages from the server
    threading.Thread(target=receive_messages, daemon=True).start()

    print("Connected to server. Type /channel <name> to join a channel.")

    # Send user input to the server
    while True:
        msg = input()
        if msg:
            client.send(msg.encode())


# Main entry point for script
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python chat.py server | client")
        sys.exit(1)

    mode = sys.argv[1].lower()
    
    if mode == "server":
        start_server()
    elif mode == "client":
        start_client()
    else:
        print("Invalid mode. Use 'server' or 'client'.")

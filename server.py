import socket

import select

from common import PORT, _receive_one, _make_raw_message


class ChatServer:
    def __init__(self, port=PORT):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('', port))
        self.server_socket.listen(1024)
        self.server_socket.setblocking(False)
        self.clients = []
        self.username_by_socket = dict()
        print(f"Server started on port {port}")

    def broadcast_message(self, sock, message):
        raw_message = _make_raw_message(message)
        for client_socket in self.clients:
            # if client_socket != sock: # If we don't want to notify the sender we need this line.
            try:
                print(client_socket.send(raw_message))
            except Exception as e:
                print(f"Failed to send message to {client_socket}: {e}")
                print(f"Removing client {client_socket}")
                self.remove(client_socket)

    def remove(self, client_socket):
        client_socket.close()
        self.clients.remove(client_socket)
        del self.username_by_socket[client_socket]

    def run(self):
        try:
            while True:
                # We introduce a 10 seconds timeout on select to allow for graceful shutdown on Windows.
                read_sockets, _, exception_sockets = select.select([self.server_socket] + self.clients, [],
                                                                   self.clients, 10)

                for notified_socket in read_sockets:
                    if notified_socket == self.server_socket:
                        self._accept_incoming()
                    else:
                        self._recv_one_and_broadcast(notified_socket)

                for notified_socket in exception_sockets:
                    self.remove(notified_socket)

        except KeyboardInterrupt:
            print("Server shutting down...")
            self.server_socket.close()

    def _recv_one_and_broadcast(self, client_socket):
        try:
            message = _receive_one(client_socket)
            if not len(message):
                print(f"Closed connection from {client_socket.getpeername()}")
                self.remove(client_socket)
                return

            username = self.username_by_socket[client_socket]
            if username is None:
                self.username_by_socket[client_socket] = message
                message += ' has entered the chat !'  # announce join

            self.broadcast_message(client_socket, f"{username or ''} > " + message)
        except Exception as e:
            print(f"Exception from {client_socket.getpeername()}: {e}")
            self.remove(client_socket)

    def _accept_incoming(self):
        client_socket, client_address = self.server_socket.accept()
        client_socket.setblocking(False)
        self.clients.append(client_socket)
        self.username_by_socket.setdefault(client_socket)
        print(f"Accepted new connection from {client_address[0]}:{client_address[1]}")

def start_server(port=PORT):
    return ChatServer(port).run()



if __name__ == "__main__":
    start_server()

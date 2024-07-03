import socket
import select
import struct

from common import btoi, HEADER_LENGTH, PORT, _receive_one, itob, _make_raw_message


class ChatServer:
    def __init__(self, port):
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
            # if client_socket != sock: - if we don't want to notify the sender we need this if.
            try:
                print(client_socket.send(raw_message))
            except Exception as e:
                print(f"Failed to send message to {client_socket}: {e}")
                print(f"Removing client {client_socket}")

                client_socket.close()
                self.clients.remove(client_socket)

    def run(self):
        try:
            while True:
                # We introduce a 10 seconds timeout on select to allow for graceful shutdown on Windows.
                read_sockets, _, exception_sockets = select.select([self.server_socket] + self.clients, [], self.clients, 10)

                for notified_socket in read_sockets:
                    if notified_socket == self.server_socket:
                        client_socket, client_address = self.server_socket.accept()
                        client_socket.setblocking(False)
                        self.clients.append(client_socket)
                        self.username_by_socket.setdefault(client_socket)
                        print(f"Accepted new connection from {client_address[0]}:{client_address[1]}")
                    else:
                        try:
                            message = _receive_one(notified_socket)
                            if not len(message):
                                print(f"Closed connection from {notified_socket.getpeername()}")
                                self.clients.remove(notified_socket)
                                notified_socket.close()
                                continue

                            username = self.username_by_socket[notified_socket]
                            if username:
                                self.broadcast_message(notified_socket, f"{username} > " + message)
                            else:
                                self.username_by_socket[notified_socket] = message
                                self.broadcast_message(notified_socket, f' > {message} has entered the chat !')
                        except Exception as e:
                            print(f"Exception from {notified_socket.getpeername()}: {e}")
                            self.clients.remove(notified_socket)
                            notified_socket.close()

                for notified_socket in exception_sockets:
                    self.clients.remove(notified_socket)
                    notified_socket.close()

        except KeyboardInterrupt:
            print("Server shutting down...")

            self.server_socket.close()

if __name__ == "__main__":
    server = ChatServer(PORT)
    server.run()

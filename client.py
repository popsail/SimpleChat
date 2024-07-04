import socket
import errno
import sys
import threading
import random

from common import PORT, IP, handle_error, _receive_one, _make_raw_message


class ChatClient:
    def __init__(self, username, ip=IP, port=PORT, blocking=False):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((ip, port))
        self.client_socket.setblocking(blocking)
        self.username = username
        self.send_message(username)

    def setblocking(self, _flag):
        return self.client_socket.setblocking(_flag)

    def send_message(self, message):
        if message:
            raw_message = _make_raw_message(message)
            self.client_socket.send(raw_message)


    def stream_received_messages(self,out=sys.stdout):
        while True:
            message = self.receive_one()
            if message:
                print(f"{message}", file=out)


    def receive_one(self):
        '''If this function returns None, it means EWOULDBLOCK'''
        try:
            message = _receive_one(self.client_socket)
            if not message:
                return handle_error("Connection closed by the server")

            return message

        except IOError as e:
            if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
                return handle_error(f"Reading error: {str(e)}")

        except Exception as e:
            return handle_error(f"General error: {str(e)}")



    def run(self):
        receive_thread = threading.Thread(target=self.stream_received_messages)
        receive_thread.daemon = True
        receive_thread.start()

        try:
            while receive_thread.is_alive():
                message = input()  # We'd want to  properly prompt the user, but that would require using a more advanced UI.
                self.send_message(message)

        except (KeyboardInterrupt, ConnectionResetError):
            print("Exiting...") # ConnectionReset is handled by receiver thread.


if __name__ == "__main__":
    if len(sys.argv) != 2:
        username = "Guest" + str(random.randint(10, 99))
    else:
        username = sys.argv[1]

    client = ChatClient(username, IP, PORT)
    client.run()

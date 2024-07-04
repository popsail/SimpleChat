import sys

IP = "127.0.0.1"
HEADER_LENGTH = 4  # int32
PORT = 12345


def btoi(bytes):
    return int.from_bytes(bytes, 'big', signed=False)


def itob(i: int):
    if i < 0: raise ValueError("wat")

    return i.to_bytes(4, 'big', signed=False)


def handle_error(err):
    print(err, file=sys.stderr)
    sys.exit(1)


def _receive_one(socket, header_length=HEADER_LENGTH):
    header = socket.recv(header_length)

    if not len(header):
        return None

    message_length = btoi(header)
    return socket.recv(message_length).decode('utf-8')


def _make_raw_message(message):
    encoded_message = message.encode('utf-8')
    message_header = itob(len(encoded_message))
    return message_header + encoded_message

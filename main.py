import os
import random
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from contextlib import contextmanager

from AIClient import AIClient, start_ai_client
from client import ChatClient
from server import ChatServer, start_server


def mute():
    sys.stdout = open(os.devnull, 'w')

def main():
    pool = ProcessPoolExecutor(initializer=mute)
    pool.submit(start_server)
    time.sleep(1) # let server go online
    [pool.submit(start_ai_client, 'message', 4) for _ in range(2)]
    [pool.submit(start_ai_client, 'time', 5, start_after=random.random()*8) for _ in range(2)]
    ChatClient("USER").run()
    pool.shutdown()


if __name__ == '__main__':
    main()



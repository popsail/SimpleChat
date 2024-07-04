import os
import random
import sys
import time
from concurrent.futures import ProcessPoolExecutor

from AIClient import start_ai_client
from client import ChatClient
from server import start_server


def initializer():
    sys.stdout = open(os.devnull, 'w')

def main():

    try:
        pool = ProcessPoolExecutor(initializer=initializer)
        pool.submit(start_server)
        time.sleep(1) # let server go online
        [pool.submit(start_ai_client, 'message', 4) for _ in range(2)]
        [pool.submit(start_ai_client, 'time', 5, start_after=random.random()*8) for _ in range(2)]
        ChatClient("USER").run()

    except KeyboardInterrupt: # TODO: ProcessPoolExecutor shutdown is a disgrace to humanity, find a way to overcome it.
        print("Exiting...")



if __name__ == '__main__':
    main()



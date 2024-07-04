import random
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import openai
import threading

from client import ChatClient
from common import IP, PORT

# Set your OpenAI API key
openai.api_key = 'your_openai_api_key'


class AIClient(ChatClient):
    def __init__(self, ip, port, username, mode, n, api_key=None):
        super().__init__(ip, port, username, blocking=mode=='message')
        self.mode = mode
        self.n = n
        self.api_key = api_key

        if self.api_key:
            openai.api_key = self.api_key

    def generate_response(self, prompt):
        print(prompt)
        return "STUBRESPONSE"
        # response = openai.Completion.create(
        #     engine="gpt-4",  # Specify the correct engine
        #     prompt=prompt,
        #     max_tokens=150
        # )
        # return response.choices[0].text.strip()

    def start_monitor_messages(self):
        message_count = 0
        buffer = []
        while True:
            message = self.receive_one()
            buffer.append(message)
            if message:
                message_count += 1
                if message_count >= self.n:
                    message_count = -1 # Ignore our own message when counting
                    prompt = self.create_prompt_from_conversation(buffer)
                    response = self.generate_response(prompt)
                    self.send_message(response)

                    buffer.clear() # Consider a trimming parameter instead?

    def create_prompt_from_conversation(self, conversation):
        conversation_str = '\n'.join(conversation)
        prompt = f"""I'm in a chat room. my username in the chat is ${self.username}.
I'm going to forward whatever you write as is, so whatever you write will appear as coming from my username.
(Don't write the username prefix in your response)
Respond in a witty manner to the following messages of the chat:
${conversation_str}"""
        return prompt

    def start_periodic_messages(self):
        while True:
            time.sleep(self.n) # This is unreliable on longer time scales
            response = self.generate_response(
                "I'm on a chat. I'm gonna forward whatever you write as is. write something funny:")
            self.send_message(response)

    def run(self):
        if self.mode == 'message':
            self.start_monitor_messages()
        elif self.mode == 'time':
            self.start_periodic_messages()


if __name__ == "__main__":
    clients = []
    if len(sys.argv) != 4:
        clients.append(AIClient(IP, PORT, "AI_T" + str(random.randint(10, 99)), 'time', 5))
        clients.append(AIClient(IP, PORT, "AI_M" + str(random.randint(10, 99)), 'message', 3))
    else:
        username = sys.argv[1]
        mode = sys.argv[2]  # 'message' or 'time'
        n = int(sys.argv[3])
        clients.append(AIClient(IP, PORT, username, mode, n))


    with ThreadPoolExecutor() as executor:
        for client in clients:
            executor.submit(client.run)



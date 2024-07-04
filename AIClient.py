import concurrent
import inspect
import random
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import openai
import os

from openai import OpenAIError

from client import ChatClient
from common import IP, PORT

try:
    from dotenv import load_dotenv
    load_dotenv()
except: # if dotenv is installed great, if not nvm.
    pass

from openai import OpenAI

def make_oaiclient(api_key=None):
    try:
        return OpenAI(api_key=api_key)  # pass api_key or set OPENAI_API_KEY (use .env)
    except OpenAIError:
        return None


class AIClient(ChatClient):
    def __init__(self, mode, n, username=None, oai_api_key=None, port=PORT, ip=IP, start_after=0):
        if not username:
            username = "AI_" + mode[:1] + str(random.randint(100, 999))

        super().__init__(username, ip, port, blocking=mode == 'message')
        self.mode = mode
        self.n = n
        self.oaiclient = make_oaiclient(oai_api_key)
        self.stub_responses = [
            'How are you?',
            "This is totally random",
            "I've noticed you around",
            "This is a stub response"
        ]
        self.start_after = start_after

    def generate_response(self, prompt):
        print(prompt)
        response = self.oaiclient.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are in a chat - only respond with your chat text response"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            max_tokens=200
        ).choices[0].message.content.strip() if self.oaiclient else random.choice(self.stub_responses)

        print(response)

        return response

    def start_monitor_messages(self):
        message_count = 0
        buffer = []
        while True:
            message = self.receive_one()
            buffer.append(message)
            if message:
                message_count += 1
                if message_count >= self.n:
                    message_count = -1  # Ignore our own message when counting
                    prompt = self.create_prompt_from_conversation(buffer)
                    response = self.generate_response(prompt)
                    print("M", response)
                    self.send_message(response)

                    buffer.clear()  # Consider a trimming parameter instead?

    def create_prompt_from_conversation(self, conversation):
        conversation_str = '\n'.join(conversation)
        prompt = f"""I'm in a chat room. my username in the chat is ${self.username}.
I'm going to forward whatever you write as is, so whatever you write will appear as coming from my username.
(Don't write the username prefix in your response)
Respond in a witty manner to the following messages of the chat:
${conversation_str}"""
        return prompt

    def start_periodic_messages(self):
        previous_response = ""
        while True:
            time.sleep(self.n)  # This is unreliable on longer time scales
            previous_response = self.generate_response(
                f"""I'm on a chat.
I'm gonna forward whatever you write as-is so don't mention anything about prompts/chats/AI but just spew out text I can forward to the chat.
Your previous response was: {previous_response}
write something witty and unrelated to your previous response:""")
            self.send_message(previous_response)

    def run(self):
        try:
            time.sleep(self.start_after) # just a util to prevent time-synchronization between periodic bots.
            if self.mode == 'message':
                self.start_monitor_messages()
            elif self.mode == 'time':
                self.start_periodic_messages()
        except KeyboardInterrupt:
            print("We're outta here")


def start_ai_client(*args, **kwargs):
    return AIClient(*args, **kwargs).run()


if __name__ == "__main__":
    clients = []
    if len(sys.argv) != 4:
        clients.append(AIClient('time', 5, "AI_T" + str(random.randint(10, 99)), port=PORT, ip=IP))
        clients.append(AIClient('message', 3, "AI_M" + str(random.randint(10, 99)), port=PORT, ip=IP))
    else:
        username = sys.argv[1]
        mode = sys.argv[2]  # 'message' or 'time'
        n = int(sys.argv[3])
        clients.append(AIClient(mode, n, username, port=PORT, ip=IP))


    with ThreadPoolExecutor() as executor:
        futures = []
        for client in clients:
            futures.append(executor.submit(client.run))

        for completed in concurrent.futures.as_completed(futures): # debug exceptions
            completed.result()


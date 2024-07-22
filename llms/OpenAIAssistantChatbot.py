import json
import time
import openai

API_KEY = "SET YOUR API KEY"


class OpenAIAssistantChatbot:
    def __init__(self, assistant_id) -> None:
        self.api_key = API_KEY
        self.client = openai.OpenAI(api_key=self.api_key)
        self.assistant = self.client.beta.assistants.retrieve(assistant_id)
        self.total_tokens = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0


    def createNewAssistant(self, instructions: str) -> None:
        # print_to_console("Creating assistant")
        self.assistant = self.client.beta.assistants.create(
            name="Assistant",
            instructions=instructions,
            model="gpt-3.5-turbo"
        )

    def createThread(self) -> None:
        self.thread = self.client.beta.threads.create()

    def appendMessage(self, message) -> None:
        self.client.beta.threads.messages.create(
            thread_id=self.thread.id,
            role="user",
            content=message
        )

    def Run(self, print_response=True) -> str:
        self.run = self.client.beta.threads.runs.create(
            thread_id=self.thread.id,
            assistant_id=self.assistant.id,
            max_completion_tokens=500
        )
        if print_response:
            return self.wait_for_response(100)
        else:
            return self.wait_for_response(100, False)

    def wait_for_response(self, timeout, print_response=True) -> str:
        start_time = time.time()
        while time.time() - start_time < timeout:
            self.run = self.client.beta.threads.runs.retrieve(thread_id=self.thread.id, run_id=self.run.id)
            if self.run.completed_at is not None:
                if print_response:
                    self.print_response()
                self.total_tokens = self.total_tokens + self.run.usage.total_tokens
                self.prompt_tokens = self.prompt_tokens + self.run.usage.prompt_tokens
                self.completion_tokens = self.completion_tokens + self.run.usage.completion_tokens
                return self.run.model_dump_json()
            time.sleep(1)
        return "Timeout"

    def print_response(self) -> None:
        try:
            message = self.client.beta.threads.messages.list(thread_id=self.thread.id).data[0]
            message_json = json.loads(message.model_dump_json())
            content = message_json['content']
            item = content[0]
            print(item['text']['value'])
        except:
            print("Error: No JSON response found.")

    def get_response_json(self) -> str:
        message = self.client.beta.threads.messages.list(thread_id=self.thread.id).data[0]
        message_json = json.loads(message.model_dump_json())
        content = message_json['content']
        item = content[0]
        return self.clean_json_string(item['text']['value'])

    def get_response_text(self) -> str:
        message = self.client.beta.threads.messages.list(thread_id=self.thread.id).data[0]
        message_json = json.loads(message.model_dump_json())
        content = message_json['content']
        item = content[0]
        return item['text']['value']

    def clean_json_string(self, s) -> str:
        if s.startswith('{') and s.endswith('}'):
            return s.strip()
        else:
            start_index = s.find('{')
            end_index = s.rfind('}') + 1
            if start_index != -1 and end_index != -1:
                return s[start_index:end_index]
            else:
                return s  # oder Fehlerbehandlung, falls gewünscht

    def remove_message(self):
        self.client.beta.threads.messages.delete(thread_id=self.thread.id, message_id=
        self.client.beta.threads.messages.list(thread_id=self.thread.id).data[1].id)

    def Run_JSON(self, message: str) -> dict:
        self.createThread()
        self.appendMessage(message)
        self.Run()
        return json.loads(self.get_response_json())

    @staticmethod
    def ask_local_model(message: str):
        # Point to the local server
        client = openai.OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")

        completion = client.chat.completions.create(
            model="Qwen/Qwen2-7B-Instruct-GGUF",
            messages=[
                {"role": "user", "content": message}
            ],
            temperature=0.001,
            top_p=0.9
        )
        return completion.choices[0].message

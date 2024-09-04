import os
from pathlib import Path

import litellm
from litellm import completion, completion_cost

litellm.modify_params = True
os.environ["OPENAI_API_KEY"] = Path("openai_key.txt").read_text().strip()
# os.environ["ANTHROPIC_API_KEY"] = Path("anthropic_key.txt").read_text().strip()

class Prompt:
    def __init__(self):
        self.messages = []
        self.total_cost = 0

    def add_message(self, message: str, role="user"):
        if role not in ["user", "assistant", "system"]:
            raise ValueError(
                f"Invalid role: {role}. Roles are 'user', 'assistant', 'system'"
            )

        self.messages.append({"role": role, "content": message})
        return self

    def run(self, model, should_print=True) -> str:
        response = completion(
            model=model,
            messages=self.messages,
        )
        response_text = response["choices"][0]["message"]["content"]
        self.add_message(response_text, role="assistant")
        if should_print:
            print(f"Bot: {response_text}\n\n")

        self.total_cost += completion_cost(completion_response=response)
        return response_text


system_message = ""
memory_window_size = 5

past_messages = []
if system_message:
    past_messages.append({"role": "system", "content": system_message})


def converse(initial_message: str = None, model: str = "gpt-4o-2024-08-06"):
    if initial_message:
        past_messages.append({"role": "user", "content": initial_message})

    # make new log file
    new_log_number = len(list(Path("logs").glob("log*.txt"))) + 1
    log_path = Path("logs") / f"log_{new_log_number}.txt"
    log_path.parent.mkdir(exist_ok=True)
    with open(log_path, "w+") as f:
        f.write(
            "\n".join(
                [
                    f"{message['role']}: {message['content']}"
                    for message in past_messages
                ]
            )
        )

        if initial_message:
            response = completion(
                model=model,
                messages=past_messages,
            )
            response_text = response["choices"][0]["message"]["content"]
            response_message = {"role": "assistant", "content": response_text}
            save_message(file=f, message=response_message)

            print(f"Bot: {response_text}\n\n")

        while True:
            user_input = input("You: ")
            if user_input == "quit":
                print("DONE")
                break
            user_message = {"role": "user", "content": user_input}
            save_message(file=f, message=user_message)

            response = completion(
                model=model,
                messages=past_messages,
            )
            response_text = response["choices"][0]["message"]["content"]
            response_message = {"role": "assistant", "content": response_text}
            save_message(file=f, message=response_message)

            print(f"Bot: {response_text}\n\n")


def save_message(file, message: dict):
    past_messages.append(message)
    file.write(f"\n{message['role']}: {message['content']}")

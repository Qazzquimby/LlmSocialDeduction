

import random

models = [
    "gpt-4o-2024-08-06",
    "gpt-4o-mini-2024-07-18",
    "claude-3-5-sonnet-20240620",
    "openrouter/nousresearch/hermes-3-llama-3.1-405b",
    "openrouter/google/gemini-pro-1.5",
    "openrouter/meta-llama/llama-3.1-405b-instruct",
    "openrouter/gryphe/mythomax-l2-13b",
    "openrouter/meta-llama/llama-3.1-70b-instruct",
    "openrouter/microsoft/wizardlm-2-8x22b",
    "openrouter/mistralai/mixtral-8x22b-instruct"
]

def get_random_model():
    return random.choice(models)

# info = litellm.get_model_info(model)



import random

models = [
    "gpt-4o-2024-08-06",
    "gpt-4o-mini-2024-07-18",
    "claude-3-5-sonnet-20240620",
]

def get_random_model():
    return random.choice(models)

# info = litellm.get_model_info(model)

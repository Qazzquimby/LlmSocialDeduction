import random

models = [
    # "openrouter/openai/gpt-4o",
    "openrouter/openai/gpt-4o-mini",
    # "openrouter/meta-llama/llama-3.1-8b-instruct:free",
    # "openrouter/nousresearch/hermes-3-llama-3.1-405b:free", # broke?
    # "openrouter/meta-llama/llama-3.1-405b-instruct",
    # "gpt-4o-2024-08-06",
    # rejects vv
    # "gpt-4o-mini-2024-07-18",
    # "claude-3-5-sonnet-20240620", # Public Relations
    # "openrouter/nousresearch/hermes-3-llama-3.1-405b",
    # "openrouter/google/gemini-pro-1.5", # seems crashy?
    # "openrouter/gryphe/mythomax-l2-13b", # seems really dumb
    # "openrouter/meta-llama/llama-3.1-70b-instruct",
    # "openrouter/microsoft/wizardlm-2-8x22b", # seems crashy
    # "openrouter/mistralai/mixtral-8x22b-instruct"
]


def get_random_model():
    return random.choice(models)


# info = litellm.get_model_info(model)

import os
from dotenv import load_dotenv

from agentx.model.ai.local.llama_cpp.llamacpp import LlamaCpp

# ``override=True`` makes the ``.env`` authoritative — see ``main.py`` for the
# full rationale (stale shell exports would otherwise mask the file's value,
# breaking local llamacpp model loading the same way they broke NIM keys).
load_dotenv(override=True)

LLAMA_CPP_MODEL_QWEN_2_5 = "Qwen2.5-1.5B-Instruct-GGUF"
LLAMA_CPP_MODEL_QWEN_3 = "Qwen3-4B-GGUF"
LLAMA_CPP_MODEL_NEMOTRON_3_NANO = "nvidia/NVIDIA-Nemotron-3-Nano-4B-GGUF"
LLAMA_CPP_MODEL_QWEN_3_5 = "Jackrong/Qwen3.5-2B-Claude-4.6-Opus-Reasoning-Distilled-GGUF:Q5_K_S"
LLAMA_CPP_MODELS_CACHE_PATH = "LLAMA_CPP_MODELS_CACHE_PATH"

model_factory_llamacpp = LlamaCpp(os.environ[LLAMA_CPP_MODELS_CACHE_PATH])
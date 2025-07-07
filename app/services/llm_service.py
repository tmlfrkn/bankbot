from functools import lru_cache
import os
from asyncio import to_thread

from ctransformers import AutoModelForCausalLM  # type: ignore

@lru_cache(maxsize=1)
def load_llm():
    model_path = os.getenv(
        "YI_MODEL_PATH", "./models/yi-1.5-9b-chat/Yi-1.5-9B-Chat-Q4_K_M.gguf"
    )
    return AutoModelForCausalLM.from_pretrained(
        model_path,
        model_type="llama",
        gpu_layers=32,  # default CPU; adjust by env
        context_length=4096,
        max_new_tokens=150,
        temperature=0.3,
        threads=8,
    )


def generate_answer(llm, query: str, context: str) -> str:
    print(f"Generating answer for query: {query}")
    prompt = f"""
[INST]
You are BankBot, an enterprise banking assistant.
TASK:
1. Answer the user question as accurately and concisely as possible USING ONLY the information provided in the context below.
2. Write the answer in the SAME LANGUAGE as the question.
3. When you reference a specific fact from a source chunk, append the corresponding citation label in square brackets, e.g. [1] or [2].
4. After the answer, add a new line that begins with "*Citation:" followed by the EXACT citation strings for each label you used, separated by "; ". Citation strings are provided inside the context next to each chunk.
5. If the required information is NOT present in the context, reply with exactly: "I don't have enough information in my current knowledge base to answer that."

# Context
{context}

# Question
{query}
[/INST]
"""
    return llm(prompt).strip()


async def generate_answer_async(llm, query: str, context: str) -> str:
    """Run LLM generation in background thread to avoid blocking event loop."""
    return await to_thread(generate_answer, llm, query, context) 
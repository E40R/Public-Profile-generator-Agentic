import os
import time
from dotenv import load_dotenv

load_dotenv()


def get_llm(temperature: float = 0.0, use_pro: bool = False):
    """Initializes and returns the appropriate LangChain chat model based on environment keys."""
    # Check for Google Gemini keys first
    google_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if google_key:
        if "GOOGLE_API_KEY" not in os.environ:
            os.environ["GOOGLE_API_KEY"] = google_key
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            model_name = "gemini-2.0-flash"
            return ChatGoogleGenerativeAI(
                model=model_name,
                temperature=temperature,
                timeout=12,           # Fast 12 second timeout
                max_retries=0         # No internal retries if quota exceeded
            )
        except Exception as e:
            print(f"[LLM Init] Error initializing ChatGoogleGenerativeAI: {e}")

    # Check for Hugging Face free models
    hf_token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACEHUB_API_TOKEN")
    if hf_token:
        try:
            from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
            endpoint = HuggingFaceEndpoint(
                repo_id="mistralai/Mistral-7B-Instruct-v0.3",
                temperature=max(temperature, 0.01),
                huggingfacehub_api_token=hf_token
            )
            return ChatHuggingFace(llm=endpoint)
        except Exception as e:
            print(f"[LLM Init] Error initializing HuggingFace model: {e}")

    # Check for OpenAI keys
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        try:
            from langchain_openai import ChatOpenAI
            model_name = "gpt-4o" if use_pro else "gpt-4o-mini"
            return ChatOpenAI(model=model_name, temperature=temperature)
        except Exception as e:
            print(f"[LLM Init] Error initializing ChatOpenAI: {e}")

    raise ValueError(
        "No valid AI API key found! Please set GOOGLE_API_KEY, HF_TOKEN, or OPENAI_API_KEY in your environment or .env file."
    )


def invoke_with_retry(chain, inputs: dict, max_retries: int = 1, base_delay: float = 0.5):
    """Invoke a chain with fast failover on quota/rate limit errors."""
    for attempt in range(max_retries):
        try:
            return chain.invoke(inputs)
        except Exception as e:
            error_str = str(e)
            # If rate limit or quota exceeded, fail immediately to fallback instead of sleeping for minutes
            if any(kw in error_str for kw in ["429", "RESOURCE_EXHAUSTED", "quota", "rate", "404", "no longer available"]):
                raise
            else:
                if attempt < max_retries - 1:
                    time.sleep(base_delay)
                else:
                    raise
    raise Exception(f"All {max_retries} retry attempts failed")

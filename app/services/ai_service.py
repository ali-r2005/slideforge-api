import json
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

from dotenv import load_dotenv
import os

load_dotenv()


llm = ChatOpenAI(
    model=os.getenv("OPENROUTER_MODEL"),
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    temperature=0.7
)
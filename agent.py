from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, AzureChatOpenAI
from langchain_deepseek import ChatDeepSeek
from langchain_core.prompts import ChatPromptTemplate
from models import Question, Response
import os

load_dotenv()

def get_available_llms():
    # Return all available LLMs regardless of API keys
    # The connection error will be handled when actually trying to use the LLM
    return ["GPT-o3-mini", "GPT-o1", "Deepseek-R1", "Azure-GPT-4o-mini"]

def get_llm(llm_name):
    if llm_name in ["GPT-o3-mini", "GPT-o1"]:
        if not os.getenv('OPENAI_API_KEY'):
            raise ValueError("OpenAI API key not configured. Please add it in Settings.")
        return ChatOpenAI(
            model=llm_name.lower(),
            temperature=0,
            streaming=True
        )
    elif llm_name == "Deepseek-R1":
        if not os.getenv('DEEPSEEK_API_KEY'):
            raise ValueError("Deepseek API key not configured. Please add it in Settings.")
        return ChatDeepSeek(
            model=llm_name.lower(),
            temperature=0,
            streaming=True
        )
    elif llm_name == "Azure-GPT-4o-mini":
        if not os.getenv('AZURE_OPENAI_API_KEY'):
            raise ValueError("Azure OpenAI API key not configured. Please add it in Settings.")
        return AzureChatOpenAI(
            azure_deployment="gpt-4o-mini",
            api_version="2024-10-21",
            streaming=True
        )
    raise ValueError(f"Unknown LLM: {llm_name}")

def process_session_data(session):
    formatted_data = ""
    for question in session.questions:
        formatted_data += f"## Question: {question.text}\n"
        if question.responses:
            formatted_data += "## Responses:\n"
            for response in question.responses:
                formatted_data += f'''- ```{response.text}```\n'''
        formatted_data += "\n"
    return formatted_data

def generate_insights(agent_prompt, llm_name, session_data):
    llm = get_llm(llm_name)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", agent_prompt),
        ("human", f"# Here are the sticky note questions and responses:\n\n{session_data}")
    ])
    
    chain = prompt | llm
    # print("==============================================")
    # print("Agent Prompt: ", agent_prompt)
    # print("==============================================")
    # print("Session Data: ", session_data)
    # print("==============================================")
    response = chain.invoke({"input": session_data})
    # print(response)
    return response.content
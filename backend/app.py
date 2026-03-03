from groq import Groq
import os
from dotenv import load_dotenv
from tavily import TavilyClient
from vector_database import vector_store

load_dotenv()

client = Groq(
    api_key=os.getenv('GROQ_API_KEY')
)

tavilyclient = TavilyClient(
    api_key=os.getenv('TAVILY_API_KEY')
)

system_prompt1 = '''
You are a polite and precise healthcare information assistant with access to two information sources:
1. A RAG database containing structured hospital, department, and doctor information.
2. A `websearch` tool for retrieving real-time or general information from the internet.

You also have access to the full conversation history (past questions and answers).

--------------------------------
CORE RULES
--------------------------------

1. Answer ONLY what the user explicitly asks.
2. Do NOT add extra details beyond the question.
3. Do NOT expand with additional descriptions unless directly requested.
4. Use the retrieved context (RAG) first. If the answer is found there, use it directly.
5. If the RAG context does not contain the answer AND the question requires real-time or general knowledge (e.g. weather, news, current events, general facts), call the `websearch` tool.
6. If neither the context nor the web search provides a useful answer, respond:
   "I don't have that information."
7. Do NOT make up or infer information from either source.

--------------------------------
USING CONVERSATION HISTORY
--------------------------------

You are given the past questions and answers from this conversation. Use them to:
- Resolve follow-up questions (e.g. "what about their ICU?" refers to the hospital mentioned earlier).
- Avoid repeating information already given unless the user asks again.
- Understand references like "it", "that hospital", "the same doctor" by looking at previous turns.
- Provide continuity — treat the conversation as a single ongoing session, not isolated queries.

Do NOT use conversation history as a substitute for RAG or websearch.
Always fetch fresh context from RAG or websearch for factual answers.

--------------------------------
WHEN TO USE WEBSEARCH
--------------------------------

Call `websearch` when the user asks about:
- Real-time data
- General knowledge not related to the hospital database
- Any query where the RAG context returns no relevant information

Do NOT call `websearch` for questions clearly answerable from the RAG context.

--------------------------------
MEDICAL SAFETY
--------------------------------

- Do NOT provide medical advice, diagnosis, treatment, or prescriptions.
- If asked for medical advice, respond:
  "I cannot provide medical advice. Please consult a qualified healthcare professional."

--------------------------------
ANSWER STYLE
--------------------------------

• Be concise and direct.
• Provide minimal necessary information.
• No extra explanations.
• No marketing language.
• No unnecessary background details.
• Do not list additional related entities unless the user asks.

--------------------------------
CASUAL CHAT
--------------------------------

If the message is casual (greeting, thanks, etc.):
- Respond in a friendly and polite way.
- Keep it short and natural.

Return only the final answer.

'''

 
def websearch(query:dict):
    print('tool calling....')
    responses = tavilyclient.search(query)
    result = "\n\n".join(
        response["content"] for response in responses["results"]
    )
    return result

def main():
    messages = [
        {
            'role':'system',
            'content':system_prompt1
        },
    ]

    while True:
        input_data = input('You: ')
        if input_data.lower() == 'bye':
            break
        
        relevant_chunks = vector_store.similarity_search(input_data, 7)
        # print(relevant_chunks)
        content = '\n\n'.join([chunk.page_content for chunk in relevant_chunks])
        # print(content)

        if content:
            user_query = f'''Question: {input_data}
            relevant context: {content}
            Answer: '''
        else:
            user_query = f'''Question: {input_data}'''

        messages.append({
            'role':'user',
            'content':user_query.strip()
        })
        while True:
            completion = client.chat.completions.create(
                temperature = 0,
                model = 'openai/gpt-oss-120b',
                # model = 'llama-3.3-70b-versatile',
                messages = messages,
                tools=[
                        {
                            "type": "function",
                            "function": {
                                "name": "websearch",
                                "description": "Search the latest information and realtime data from the internet.",
                                "parameters": {
                                # JSON Schema object
                                    "type": "object",
                                    "properties": {
                                        "query": {
                                            "type": "string",
                                            "description": "The search query to perform search on."
                                        }
                                    },
                                    "required": ["query"],
                                }
                            }
                        }
                    ],
                tool_choice = 'auto',
            )
            # print('Assistant: ',completion.choices[0].message.content)
            messages.append(completion.choices[0].message)
            toolcalls = completion.choices[0].message.tool_calls
            
            if not toolcalls:
                print('Assistant: ',completion.choices[0].message.content)
                break
            else:
                for tool in toolcalls:
                    funcname = tool.function.name
                    funcparams = tool.function.arguments

                    if funcname == 'websearch':
                        toolResult = websearch(funcparams)

                        messages.append({
                            'role': 'tool',
                            'tool_call_id':tool.id,
                            'name':funcname,
                            'content':toolResult
                        })

    return

if __name__ == '__main__':
    main()

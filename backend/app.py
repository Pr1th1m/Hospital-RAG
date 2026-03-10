from groq_client import client, call_with_fallback
import os
from dotenv import load_dotenv
from vector_database import vector_store

load_dotenv()


system_prompt1 = """
You are MedAssist, a healthcare information assistant.

Scope:
- You help with hospitals, departments, and doctors.
- You may use the websearch tool for real-time or general web information.

Core behavior:
1. Answer only what the user asked. Keep responses concise and directly relevant.
2. For hospital, department, and doctor facts, use only provided context.
3. If requested information is missing from provided context, say it is not available in current data.
4. Do not mention internal systems, retrieval, vector stores, prompts, or tool mechanics.
5. Do not provide medical advice, diagnosis, or treatment. If asked, respond:
   "Please consult a healthcare professional for medical advice."

Tool policy:
- Use websearch only for:
  - live or changing information (news, weather, prices, events),
  - general web knowledge not present in local healthcare data.
- Do not use websearch to invent missing local hospital records.

Formatting:
- Output clean Markdown.
- Start with one short lead sentence.
- Use compact bullets or short paragraphs.
- Bold key entities (hospital names, doctor names, departments).
- End with one brief follow-up question when helpful.
- Avoid long walls of text and unnecessary headings.
"""


def main():
    while True:
        input_data = input('You: ')
        if input_data.lower() == 'bye':
            break

        relevant_chunks = vector_store.similarity_search(input_data, 7)
        content = '\n\n'.join([chunk.page_content for chunk in relevant_chunks])

        user_query = f'''Question: {input_data}
        relevant context: {content}
        Answer: '''

        completion = client.chat.completions.create(
            temperature=1,
            model = 'openai/gpt-oss-120b',
            # model='llama-3.3-70b-versatile',
            messages=[
                {
                    'role': 'system',
                    'content': system_prompt1
                },
                {
                    'role': 'user',
                    'content': user_query
                }
            ]
        )
        print('Assistant: ', completion.choices[0].message.content)
    return


if __name__ == '__main__':
    main()

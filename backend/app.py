from groq import Groq
import os
from dotenv import load_dotenv
from vector_database import vector_store

load_dotenv()

client = Groq(
    api_key=os.getenv('GROQ_API_KEY')
)


system_prompt1 = '''
You are a polite and precise healthcare information assistant.

You answer questions using ONLY the retrieved context.

--------------------------------
CORE RULES
--------------------------------

1. Answer ONLY what the user explicitly asks.
2. Do NOT add extra details beyond the question.
3. Do NOT expand with additional descriptions unless directly requested.
4. If the information is not found in the context, respond:
   "I don’t have that information in the database."

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
 


def main():
    while True:
        input_data = input('You: ')
        if input_data.lower() == 'bye':
            break
        
        relevant_chunks = vector_store.similarity_search(input_data,7)
        # print(relevant_chunks)
        content = '\n\n'.join([chunk.page_content for chunk in relevant_chunks])
        # print(content)

           
        user_query = f'''Question: {input_data}
        relevant context: {content}
        Answer: '''

        completion = client.chat.completions.create(
            temperature = 1,
            # model = 'openai/gpt-oss-120b',
            model = 'llama-3.3-70b-versatile',
            messages = [
                {
                    'role':'system',
                    'content':system_prompt1
                },
                {
                    'role':'user',
                    'content':user_query
                }
            ]
        )
        print('Assistant: ',completion.choices[0].message.content)
    return

if __name__ == '__main__':
    main()

from groq_client import call_with_fallback
import os
import json
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_cohere import CohereEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone
import cohere
from system_prompt import system_prompt_hospital,system_prompt_department,system_prompt_doctor,system_prompt_hospital_list,system_prompt_department_list,system_prompt_doctor_list
load_dotenv()

co = cohere.ClientV2(
    api_key=os.getenv('COHERE_API_KEY')
)
pc = Pinecone(
    api_key= os.getenv("PINECONE_API_KEY")
)
index = pc.Index(os.getenv('PINECONE_INDEX_NAME'))
index1 = pc.Index(os.getenv('PINECONE_INDEX_NAME1'))
index2 = pc.Index(os.getenv('PINECONE_INDEX_NAME2'))


embeddings = CohereEmbeddings(
    model="embed-v4.0",
)

vector_store = PineconeVectorStore(
    embedding=embeddings,
    index=index1
)

def transform_text(data,system_prompt):
    completion = call_with_fallback(
        lambda c: c.chat.completions.create(
            model = 'openai/gpt-oss-120b',
            messages=[
                {
                    'role':'system',
                    'content': system_prompt
                },
                {
                    'role':'user',
                    'content': str(data)
                }
            ]
        )
    )
    output_text = completion.choices[0].message.content
    json_output = json.loads(output_text)
    add_json_to_vector_database(json_output)

def add_json_to_vector_database(json_output):
    if isinstance(json_output, dict):
        json_output = [json_output]
    for item in json_output:
        doc = Document(
            page_content=item['page_content'],
            metadata=item['metadata']
        )
        vector_store.add_documents([doc])

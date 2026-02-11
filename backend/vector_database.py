from groq import Groq
import os
import json
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_cohere import CohereEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone
import cohere
from system_prompt import system_prompt_hospital,system_prompt_department,system_prompt_doctor,system_prompt_hospital_list,system_prompt_doctor_list
load_dotenv()

client = Groq(
    api_key= os.getenv("GROQ_API_KEY")
)
co = cohere.ClientV2(
    api_key=os.getenv('COHERE_API_KEY')
)
pc = Pinecone(
    api_key= os.getenv("PINECONE_API_KEY")
)
index = pc.Index(os.getenv('PINECONE_INDEX_NAME'))
index1 = pc.Index(os.getenv('PINECONE_INDEX_NAME1'))

embeddings = CohereEmbeddings(
    model="embed-v4.0",
)

vector_store = PineconeVectorStore(
    embedding=embeddings,
    index=index1
)

def transform_text(data,system_prompt):
    completion = client.chat.completions.create(
        # model = 'llama-3.3-70b-versatile',
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
    output_text = completion.choices[0].message.content
    json_output = json.loads(output_text)
    add_json_to_vector_database(json_output)    
    # page_part, metadata_part = output_text.split("metadata:", 1)
    # page_content = page_part.replace("page_content:", "").strip()
    # metadata = json.loads(metadata_part.strip())
    # print('page_content: ',page_content)
    # print('\n')
    # print('metadata: ',metadata)
    # print('\n')
    # add_to_vector_database(page_content,metadata)

def add_json_to_vector_database(json_output):
    for item in json_output:
        doc = Document(
            page_content=item['page_content'],
            metadata=item['metadata']
        )
        vector_store.add_documents([doc])


# def add_to_vector_database(page_content,page_metadata):
#     document = Document(
#         page_content=page_content,
#         metadata=page_metadata
#     )
#     vector_store.add_documents([document])
#     print('document',document)
    


# transform_text(department_data,system_prompt_department)
# transform_text(hospital_data,system_prompt_hospital)
# transform_text(doctor_data,system_prompt_doctor)

    
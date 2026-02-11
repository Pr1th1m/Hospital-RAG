# Product-RAG

A Retrieval-Augmented Generation (RAG) system for healthcare information management, combining FastAPI backend with vector database capabilities for intelligent querying of hospital, department, and doctor information.

## 🏗️ Architecture

This project implements a RAG pipeline that:
- Stores healthcare data (hospitals, departments, doctors) in a relational database
- Transforms and indexes data into a Pinecone vector database using Cohere embeddings
- Enables natural language queries through LLM-powered semantic search
- Provides RESTful API endpoints for data management

## 🚀 Features

- **FastAPI Backend**: RESTful API for managing healthcare entities
- **Vector Database Integration**: Pinecone for semantic search capabilities
- **LLM Integration**: Groq API with multiple model support (Llama 3.3, GPT-OSS)
- **Embeddings**: Cohere embed-v4.0 for high-quality vector representations
- **Database Models**: SQLAlchemy ORM for relational data persistence
- **Pydantic Validation**: Type-safe data models and validation

## 📁 Project Structure

```
Product-Rag/
├── backend/
│   ├── database_models/       # SQLAlchemy database models
│   │   ├── base.py
│   │   ├── database_connection.py
│   │   ├── hospital_database_model.py
│   │   ├── department_database_model.py
│   │   └── doctor_database_model.py
│   ├── pydantic_models/       # Pydantic validation models
│   │   ├── hospital_model.py
│   │   ├── department_model.py
│   │   └── doctor_model.py
│   ├── app.py                 # CLI chat interface
│   ├── main.py                # FastAPI application
│   ├── vector_database.py     # Vector DB operations
│   ├── system_prompt.py       # LLM system prompts
│   ├── requirements.txt       # Python dependencies
│   └── .env                   # Environment variables
└── README.md
```

## 🛠️ Installation

### Prerequisites

- Python 3.8+
- Pinecone account and API key
- Groq API key
- Cohere API key

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Product-Rag
   ```

2. **Install dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   
   Create a `.env` file in the `backend` directory with the following:
   ```env
   GROQ_API_KEY=your_groq_api_key
   COHERE_API_KEY=your_cohere_api_key
   PINECONE_API_KEY=your_pinecone_api_key
   PINECONE_INDEX_NAME=your_index_name
   PINECONE_INDEX_NAME1=your_second_index_name
   ```

## 🚦 Usage

### Running the FastAPI Server

```bash
cd backend
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

### Running the CLI Chat Interface

```bash
cd backend
python app.py
```

Type your questions and the assistant will respond using the vector database. Type `bye` to exit.

## 📡 API Endpoints

### Health Check
- `GET /` - Check if backend is integrated

### Hospital Management
- `POST /hospitals` - Add a new hospital
- `GET /get_hospitals` - Retrieve all hospitals and sync to vector DB

### Department Management
- `POST /departments` - Add a new department
- `GET /get_departments` - Retrieve all departments and sync to vector DB

### Doctor Management
- `POST /doctors` - Add a new doctor
- `GET /get_doctors` - Retrieve all doctors and sync to vector DB

## 🔧 Core Components

### Vector Database (`vector_database.py`)
- **Transform Text**: Converts structured data into LLM-optimized format
- **Add to Vector DB**: Indexes documents with embeddings in Pinecone
- **Embeddings**: Uses Cohere's embed-v4.0 model

### Chat Interface (`app.py`)
- **Similarity Search**: Retrieves top 7 relevant chunks from vector store
- **LLM Response**: Generates answers using Groq's Llama 3.3 70B model
- **Safety Features**: Prevents medical advice, ensures context-based responses

### API Server (`main.py`)
- **CRUD Operations**: Create and retrieve healthcare entities
- **Data Merging**: Combines related entities (hospital + department + doctor)
- **Auto-sync**: Syncs data to vector database on retrieval

## 🧠 LLM Models Used

- **Groq Models**:
  - `llama-3.3-70b-versatile` (default for chat)
  - `openai/gpt-oss-120b` (alternative)
- **Embeddings**: Cohere `embed-v4.0`

## 🔒 Safety Features

The chat assistant includes:
- **No Medical Advice**: Refuses to provide diagnosis or treatment
- **Context-Only Responses**: Answers only from retrieved information
- **Minimal Information**: Provides concise, direct answers
- **Casual Chat Support**: Handles greetings and casual interactions

## 📦 Dependencies

Key dependencies include:
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `sqlalchemy` - ORM for database
- `pydantic` - Data validation
- `langchain-pinecone` - Vector store integration
- `langchain-cohere` - Cohere embeddings
- `cohere` - Cohere API client
- `pinecone` - Pinecone vector database
- `python-dotenv` - Environment variable management

See [`requirements.txt`](backend/requirements.txt) for complete list.

## 🎯 Use Cases

- **Healthcare Information Retrieval**: Query hospital services, departments, and doctors
- **Semantic Search**: Natural language queries about medical facilities
- **Data Management**: Structured storage and retrieval of healthcare entities
- **Conversational AI**: Chat-based interface for healthcare information

## 📝 Example Queries

```
You: What hospitals are available?
Assistant: [Lists hospitals from vector database]

You: Which doctors specialize in cardiology?
Assistant: [Returns relevant cardiologists]

You: Tell me about the emergency department
Assistant: [Provides department information]
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## 📄 License

[Add your license information here]

## 👤 Author

[Add your name/contact information here]

---

**Note**: This is a healthcare information system. It does not provide medical advice, diagnosis, or treatment. Always consult qualified healthcare professionals for medical concerns.

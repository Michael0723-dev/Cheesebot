# Cheese Knowledge Chatbot

A RAG-based chatbot that answers questions about cheese products from Kimelo's shop.

## Features

- Web scraping of cheese product data
- Vector database storage using Pinecone
- RAG implementation with OpenAI GPT-4
- Modern Streamlit frontend with chat UI
- Context-aware responses with source references

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd cheese-knowledge-chatbot
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root with the following variables:
```
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Pinecone Configuration
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_ENVIRONMENT=gcp-starter
PINECONE_INDEX_NAME=cheese-knowledge
```

5. Run the Streamlit app:
```bash
streamlit run frontend/app.py
```

## Project Structure

```
project/
├── scraping/
│   └── scraper.py          # Web scraping implementation
├── data_processing/
│   └── process_data.py     # Data cleaning and processing
├── ingestion/
│   └── ingest_to_pinecone.py  # Vector database ingestion
├── retrieval/
│   └── retriever.py        # RAG retrieval implementation
├── chatbot/
│   └── rag_chain.py        # RAG chain implementation
├── frontend/
│   └── app.py             # Streamlit frontend
├── utils/
│   ├── logging.py         # Logging configuration
│   └── config.py          # Configuration management
└── requirements.txt       # Project dependencies
```

## Usage

1. Start the application using `streamlit run frontend/app.py`
2. Open your browser to the provided Streamlit URL
3. Ask questions about cheese products in the chat interface
4. View the context sources used to generate responses

## Features

- Modern, responsive chat UI
- Streaming responses for better UX
- Context display with source references
- Clear chat history option
- Informative sidebar with usage tips

## Development

- The frontend is built with Streamlit and custom CSS
- RAG implementation uses OpenAI's GPT-4 and embeddings
- Vector storage is handled by Pinecone
- Web scraping is done with Selenium

## Deployment

The application is designed to be deployed on Streamlit Cloud:

1. Push your code to a GitHub repository
2. Connect your repository to Streamlit Cloud
3. Set up the required environment variables in Streamlit Cloud
4. Deploy the application

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 
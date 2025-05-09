# Cheese Knowledge Chatbot

A RAG-based chatbot that answers questions about cheese products using vector search and GPT-4.

## Features

- Vector database storage using Pinecone
- RAG implementation with OpenAI GPT-4
- Modern Streamlit frontend with chat UI
- Context-aware responses with product details
- Image display for cheese products
- Price and product information display

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
streamlit run app.py
```

## Project Structure

```
project/
├── app.py                 # Main Streamlit application
├── chatbot/
│   ├── bot.py            # Chat session management
│   └── retriver/         # Vector store implementation
│       └── data_retriver.py
├── utils/
│   └── config.py         # Configuration management
└── requirements.txt      # Project dependencies
```

## Usage

1. Start the application using `streamlit run app.py`
2. Open your browser to the provided Streamlit URL
3. Ask questions about cheese products in the chat interface
4. View product details including:
   - Product images
   - Cheese type and brand
   - Price information
   - Product descriptions
   - Source links

## Features

- Modern, responsive chat UI with Streamlit
- Streaming responses for better UX
- Product details display with images
- Clear chat history option
- Context-aware responses
- Product source references

## Technical Implementation

- Frontend: Streamlit for the web interface
- Vector Search: Pinecone for efficient similarity search
- Language Model: OpenAI GPT-4 for response generation
- Image Handling: Pillow for image processing
- Environment Management: python-dotenv for configuration

## Development

The chatbot uses a hybrid approach:
1. Vector search to find relevant cheese products
2. GPT-4 to generate context-aware responses
3. Streamlit for a modern, interactive UI
4. Product metadata for detailed information display

## Deployment

The application can be deployed on Streamlit Cloud:

1. Push your code to a GitHub repository
2. Connect your repository to Streamlit Cloud
3. Set up the required environment variables:
   - OPENAI_API_KEY
   - PINECONE_API_KEY
   - PINECONE_ENVIRONMENT
   - PINECONE_INDEX_NAME
4. Deploy the application

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 
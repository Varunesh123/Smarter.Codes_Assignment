# Website Content Search Application

This application allows users to search through website content by providing a URL and a search query. It uses a vector database (Weaviate) to perform semantic search and returns the top 10 matches.

## Features

- Input a website URL and search query
- Fetch and parse HTML content
- Tokenize content into chunks
- Perform semantic search using vector embeddings
- Display top 10 matches with relevance scores

## Tech Stack

### Frontend
- Next.js (React)
- Tailwind CSS
- shadcn/ui components

### Backend
- FastAPI (Python)
- BeautifulSoup for HTML parsing
- Sentence Transformers for embeddings
- Weaviate as vector database

## Getting Started

### Prerequisites
- Node.js (v18+)
- Docker and Docker Compose

### Installation

1. Clone the repository
2. Install frontend dependencies:
   \`\`\`
   npm install
   \`\`\`
3. Start the backend services:
   \`\`\`
   docker-compose up -d
   \`\`\`
4. Start the frontend:
   \`\`\`
   npm run dev
   \`\`\`
5. Open your browser and navigate to `http://localhost:3000`

## Environment Variables

Create a `.env.local` file in the root directory with the following variables:

\`\`\`
BACKEND_API_URL=http://localhost:8000
\`\`\`

## How It Works

1. The user enters a website URL and a search query
2. The frontend sends this data to the Next.js API route
3. The API route forwards the request to the Python backend
4. The backend:
   - Fetches the HTML content from the URL
   - Parses and cleans the HTML
   - Splits the content into chunks of max 500 tokens
   - Generates embeddings for each chunk
   - Stores the chunks and embeddings in Weaviate
   - Performs a semantic search using the query embedding
   - Returns the top 10 matches
5. The frontend displays the results with relevance scores

## License

MIT

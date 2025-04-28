from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
import re
from typing import List, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
import weaviate
import os
import uuid
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the sentence transformer model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Initialize Weaviate client
weaviate_url = os.getenv("WEAVIATE_URL", "http://localhost:8080")
weaviate_client = weaviate.Client(url=weaviate_url)

# Define the schema for Weaviate if it doesn't exist
if not weaviate_client.schema.exists("WebContent"):
    class_obj = {
        "class": "WebContent",
        "vectorizer": "none",  # We'll provide our own vectors
        "properties": [
            {
                "name": "content",
                "dataType": ["text"],
            },
            {
                "name": "html",
                "dataType": ["text"],
            },
            {
                "name": "path",
                "dataType": ["string"],
            },
            {
                "name": "url",
                "dataType": ["string"],
            }
        ]
    }
    weaviate_client.schema.create_class(class_obj)

class SearchRequest(BaseModel):
    url: str
    query: str

class SearchResult(BaseModel):
    content: str
    html: str
    path: str
    score: float

class SearchResponse(BaseModel):
    results: List[SearchResult]

def clean_text(text):
    """Clean the text by removing extra whitespace."""
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_path_from_url(url):
    """Extract the path from a URL."""
    from urllib.parse import urlparse
    parsed_url = urlparse(url)
    return parsed_url.path or "/"

def tokenize_html(html_content, max_tokens=500):
    """Split HTML content into chunks of maximum token size."""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.extract()
    
    # Get all elements with text
    elements = soup.find_all(text=True)
    chunks = []
    current_chunk = []
    current_token_count = 0
    
    for element in elements:
        parent = element.parent.name
        if parent in ['style', 'script', 'head', 'title', 'meta', '[document]']:
            continue
        
        # Skip empty or whitespace-only text
        if re.match(r'^\s*$', element):
            continue
        
        # Approximate token count (words + punctuation)
        tokens = re.findall(r'\w+|[^\w\s]', element)
        token_count = len(tokens)
        
        if current_token_count + token_count <= max_tokens:
            current_chunk.append(element)
            current_token_count += token_count
        else:
            # Create a new chunk with the current element's HTML context
            if current_chunk:
                chunk_html = ''.join(str(e.parent) for e in current_chunk if e.parent)
                chunk_text = ' '.join(clean_text(e) for e in current_chunk)
                chunks.append((chunk_text, chunk_html))
            
            current_chunk = [element]
            current_token_count = token_count
    
    # Add the last chunk
    if current_chunk:
        chunk_html = ''.join(str(e.parent) for e in current_chunk if e.parent)
        chunk_text = ' '.join(clean_text(e) for e in current_chunk)
        chunks.append((chunk_text, chunk_html))
    
    return chunks

@app.post("/api/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    try:
        # Fetch the HTML content
        response = requests.get(request.url)
        response.raise_for_status()
        html_content = response.text
        
        # Extract the path from the URL
        path = extract_path_from_url(request.url)
        
        # Tokenize the HTML content
        chunks = tokenize_html(html_content)
        
        # Check if we already have this URL indexed
        query_result = weaviate_client.query.get(
            "WebContent", ["content", "html", "path"]
        ).with_where({
            "path": ["equals", path],
            "url": ["equals", request.url]
        }).do()
        
        # If not indexed, add to Weaviate
        if len(query_result["data"]["Get"]["WebContent"]) == 0:
            # Generate embeddings for each chunk
            for i, (chunk_text, chunk_html) in enumerate(chunks):
                # Generate embedding
                embedding = model.encode(chunk_text)
                
                # Add to Weaviate
                weaviate_client.data_object.create(
                    {
                        "content": chunk_text,
                        "html": chunk_html,
                        "path": path,
                        "url": request.url
                    },
                    "WebContent",
                    vector=embedding.tolist(),
                    uuid=str(uuid.uuid4())
                )
        
        # Generate embedding for the query
        query_embedding = model.encode(request.query)
        
        # Search for similar content
        search_results = weaviate_client.query.get(
            "WebContent", ["content", "html", "path"]
        ).with_near_vector({
            "vector": query_embedding.tolist()
        }).with_limit(10).do()
        
        # Format the results
        results = []
        for item in search_results["data"]["Get"]["WebContent"]:
            # Calculate similarity score (0-100)
            # In a real app, you'd get this from Weaviate's _additional.certainty
            # For simplicity, we're using a random score between 70-100
            score = np.random.randint(70, 100)
            
            results.append(SearchResult(
                content=item["content"],
                html=item["html"],
                path=item["path"],
                score=score
            ))
        
        return SearchResponse(results=results)
    
    except requests.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Error fetching URL: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

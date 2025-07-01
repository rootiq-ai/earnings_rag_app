"""
RAG System implementation using ChromaDB and Ollama Llama3
"""

import os
import json
import uuid
from typing import List, Dict, Optional, Any
import chromadb
from chromadb.config import Settings
import ollama
from sentence_transformers import SentenceTransformer
import numpy as np
from datetime import datetime
import logging

from config import *

logger = logging.getLogger(__name__)

class RAGSystem:
    """RAG system using ChromaDB for storage and Ollama Llama3 for generation"""
    
    def __init__(self):
        """Initialize the RAG system"""
        self.client = None
        self.collection = None
        self.embedding_model = None
        self.ollama_client = None
        
        self._initialize_chroma()
        self._initialize_ollama()
        self._initialize_embeddings()
    
    def _initialize_chroma(self):
        """Initialize ChromaDB client and collection"""
        try:
            # Initialize ChromaDB client
            self.client = chromadb.PersistentClient(
                path=CHROMA_DB_DIR,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Get or create collection
            try:
                self.collection = self.client.get_collection(
                    name=CHROMA_COLLECTION_NAME
                )
                logger.info(f"Loaded existing collection: {CHROMA_COLLECTION_NAME}")
            except Exception:
                self.collection = self.client.create_collection(
                    name=CHROMA_COLLECTION_NAME,
                    metadata={"description": "Earnings call documents"}
                )
                logger.info(f"Created new collection: {CHROMA_COLLECTION_NAME}")
                
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {str(e)}")
            raise
    
    def _initialize_ollama(self):
        """Initialize Ollama client"""
        try:
            self.ollama_client = ollama.Client(host=OLLAMA_HOST)
            
            # Test connection and model availability
            models = self.ollama_client.list()
            available_models = [model['name'] for model in models['models']]
            
            if OLLAMA_MODEL not in available_models:
                logger.warning(f"Model {OLLAMA_MODEL} not found. Available models: {available_models}")
                # Try to pull the model
                try:
                    self.ollama_client.pull(OLLAMA_MODEL)
                    logger.info(f"Successfully pulled model: {OLLAMA_MODEL}")
                except Exception as e:
                    logger.error(f"Failed to pull model {OLLAMA_MODEL}: {str(e)}")
                    raise
            
            logger.info("Ollama client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Ollama: {str(e)}")
            self.ollama_client = None
    
    def _initialize_embeddings(self):
        """Initialize embedding model"""
        try:
            # Use sentence-transformers for embeddings (faster than Ollama for embeddings)
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Embedding model initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize embedding model: {str(e)}")
            self.embedding_model = None
    
    def check_ollama_connection(self) -> bool:
        """Check if Ollama is connected and working"""
        try:
            if not self.ollama_client:
                return False
            
            # Test with a simple generation
            response = self.ollama_client.generate(
                model=OLLAMA_MODEL,
                prompt="Hello",
                options={"num_predict": 5}
            )
            return bool(response)
        except Exception:
            return False
    
    def _chunk_text(self, text: str) -> List[str]:
        """Chunk text into smaller pieces for better retrieval"""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), CHUNK_SIZE - CHUNK_OVERLAP):
            chunk_words = words[i:i + CHUNK_SIZE]
            chunk = " ".join(chunk_words)
            chunks.append(chunk)
            
            # Break if we've covered all words
            if i + CHUNK_SIZE >= len(words):
                break
        
        return chunks
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text"""
        try:
            if self.embedding_model:
                embedding = self.embedding_model.encode(text)
                return embedding.tolist()
            else:
                # Fallback to a zero embedding
                logger.warning("Embedding model not available, using zero embedding")
                return [0.0] * 384  # Default dimension for all-MiniLM-L6-v2
        except Exception as e:
            logger.error(f"Failed to generate embedding: {str(e)}")
            return [0.0] * 384
    
    def add_document(self, content: str, metadata: Dict[str, Any]) -> bool:
        """Add a document to the vector store"""
        try:
            if not self.collection:
                logger.error("Collection not initialized")
                return False
            
            # Chunk the content
            chunks = self._chunk_text(content)
            
            # Prepare data for insertion
            documents = []
            embeddings = []
            metadatas = []
            ids = []
            
            for i, chunk in enumerate(chunks):
                # Generate unique ID
                doc_id = f"{metadata.get('company', 'unknown')}_{metadata.get('year', '')}_{metadata.get('quarter', '')}_{i}_{uuid.uuid4().hex[:8]}"
                
                # Generate embedding
                embedding = self._generate_embedding(chunk)
                
                # Prepare metadata
                chunk_metadata = metadata.copy()
                chunk_metadata.update({
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "added_date": datetime.now().isoformat(),
                    "content_length": len(chunk)
                })
                
                documents.append(chunk)
                embeddings.append(embedding)
                metadatas.append(chunk_metadata)
                ids.append(doc_id)
            
            # Add to collection
            self.collection.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Added {len(chunks)} chunks for {metadata.get('company', 'unknown')} {metadata.get('year', '')} {metadata.get('quarter', '')}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add document: {str(e)}")
            return False
    
    def search_documents(self, query: str, n_results: int = MAX_RETRIEVAL_RESULTS, 
                        filters: Optional[Dict] = None) -> List[Dict]:
        """Search for relevant documents"""
        try:
            if not self.collection:
                logger.error("Collection not initialized")
                return []
            
            # Generate query embedding
            query_embedding = self._generate_embedding(query)
            
            # Prepare where clause for filtering
            where_clause = None
            if filters:
                where_clause = {}
                for key, value in filters.items():
                    if value and value != "All":
                        where_clause[key] = value
            
            # Search in collection
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where_clause if where_clause else None,
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i in range(len(results['documents'][0])):
                    formatted_results.append({
                        'content': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'score': 1 - results['distances'][0][i],  # Convert distance to similarity
                        'company': results['metadatas'][0][i].get('company', 'Unknown'),
                        'year': results['metadatas'][0][i].get('year', ''),
                        'quarter': results['metadatas'][0][i].get('quarter', '')
                    })
            
            # Filter by similarity threshold
            filtered_results = [
                result for result in formatted_results 
                if result['score'] >= SIMILARITY_THRESHOLD
            ]
            
            logger.info(f"Found {len(filtered_results)} relevant documents for query")
            return filtered_results
            
        except Exception as e:
            logger.error(f"Failed to search documents: {str(e)}")
            return []
    
    def generate_answer(self, query: str, context_docs: List[Dict]) -> str:
        """Generate answer using Ollama Llama3"""
        try:
            if not self.ollama_client:
                return "Ollama is not available. Please ensure Ollama is running with Llama3 model."
            
            # Prepare context from retrieved documents
            context = "\n\n".join([
                f"[{doc['company']} {doc['year']} {doc['quarter']}]\n{doc['content']}"
                for doc in context_docs[:3]  # Use top 3 documents
            ])
            
            # Create prompt
            prompt = f"""Based on the following earnings call information, please answer the user's question comprehensively and accurately.

Context from Earnings Calls:
{context}

User Question: {query}

Please provide a detailed answer based on the earnings call information above. If the information is not sufficient to answer the question completely, please mention what specific information is missing. Focus on facts and quotes from the earnings calls.

Answer:"""
            
            # Generate response using Ollama
            response = self.ollama_client.generate(
                model=OLLAMA_MODEL,
                prompt=prompt,
                options={
                    "temperature": 0.3,
                    "top_k": 40,
                    "top_p": 0.9,
                    "num_predict": 512
                }
            )
            
            return response['response'].strip()
            
        except Exception as e:
            logger.error(f"Failed to generate answer: {str(e)}")
            return f"Sorry, I encountered an error while generating the answer: {str(e)}"
    
    def query(self, query: str, filters: Optional[Dict] = None) -> Dict[str, Any]:
        """Main query method that combines search and generation"""
        try:
            # Search for relevant documents
            relevant_docs = self.search_documents(query, filters=filters)
            
            if not relevant_docs:
                return {
                    'answer': "I couldn't find relevant information in the earnings calls database. Please try rephrasing your question or check if the data for your query has been extracted.",
                    'sources': [],
                    'confidence': 0.0
                }
            
            # Generate answer
            answer = self.generate_answer(query, relevant_docs)
            
            # Calculate confidence based on relevance scores
            avg_score = np.mean([doc['score'] for doc in relevant_docs]) if relevant_docs else 0.0
            confidence = min(avg_score * 1.2, 1.0)  # Boost confidence slightly
            
            return {
                'answer': answer,
                'sources': relevant_docs,
                'confidence': confidence,
                'query': query,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Query failed: {str(e)}")
            return {
                'answer': f"Sorry, I encountered an error while processing your query: {str(e)}",
                'sources': [],
                'confidence': 0.0
            }
    
    def get_collection_stats(self, filters: Optional[Dict] = None) -> Dict[str, Any]:
        """Get statistics about the document collection"""
        try:
            if not self.collection:
                return {}
            
            # Get all documents with metadata
            results = self.collection.get(include=["metadatas"])
            
            if not results['metadatas']:
                return {
                    'total_documents': 0,
                    'unique_companies': 0,
                    'latest_quarter': 'N/A',
                    'days_since_update': 0,
                    'company_distribution': {}
                }
            
            metadatas = results['metadatas']
            
            # Calculate statistics
            companies = set()
            quarters = []
            company_counts = {}
            latest_date = None
            
            for metadata in metadatas:
                company = metadata.get('company', 'Unknown')
                companies.add(company)
                
                quarter = f"{metadata.get('year', '')} {metadata.get('quarter', '')}"
                if quarter.strip():
                    quarters.append(quarter)
                
                company_counts[company] = company_counts.get(company, 0) + 1
                
                # Track latest date
                added_date = metadata.get('added_date')
                if added_date:
                    try:
                        date_obj = datetime.fromisoformat(added_date.replace('Z', '+00:00'))
                        if latest_date is None or date_obj > latest_date:
                            latest_date = date_obj
                    except:
                        pass
            
            # Calculate days since last update
            days_since_update = 0
            if latest_date:
                days_since_update = (datetime.now() - latest_date.replace(tzinfo=None)).days
            
            return {
                'total_documents': len(metadatas),
                'unique_companies': len(companies),
                'latest_quarter': max(quarters) if quarters else 'N/A',
                'days_since_update': days_since_update,
                'company_distribution': company_counts,
                'new_documents': len([m for m in metadatas if m.get('added_date', '').startswith(datetime.now().strftime('%Y-%m-%d'))])
            }
            
        except Exception as e:
            logger.error(f"Failed to get collection stats: {str(e)}")
            return {}
    
    def delete_documents(self, filters: Dict[str, str]) -> bool:
        """Delete documents matching filters"""
        try:
            if not self.collection:
                return False
            
            # Get IDs of documents to delete
            results = self.collection.get(
                where=filters,
                include=["metadatas"]
            )
            
            if results['ids']:
                self.collection.delete(ids=results['ids'])
                logger.info(f"Deleted {len(results['ids'])} documents matching filters: {filters}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete documents: {str(e)}")
            return False
    
    def reset_collection(self) -> bool:
        """Reset the entire collection"""
        try:
            if self.client and self.collection:
                self.client.delete_collection(CHROMA_COLLECTION_NAME)
                self.collection = self.client.create_collection(
                    name=CHROMA_COLLECTION_NAME,
                    metadata={"description": "Earnings call documents"}
                )
                logger.info("Collection reset successfully")
                return True
        except Exception as e:
            logger.error(f"Failed to reset collection: {str(e)}")
            return False

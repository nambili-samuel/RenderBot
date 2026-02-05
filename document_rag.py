"""
RAG (Retrieval-Augmented Generation) System for Eva Geises
Processes PDF, DOCX, TXT files from GitHub repository
Provides advanced document search and retrieval
"""

import os
import re
import logging
import asyncio
import aiohttp
import hashlib
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class DocumentRAG:
    """RAG system for document-based knowledge retrieval"""
    
    def __init__(self, github_repo_url: str = None):
        """
        Initialize RAG system
        
        Args:
            github_repo_url: URL to GitHub repository with documents
                           Format: https://github.com/username/repo/tree/main/knowledge
        """
        self.github_repo_url = github_repo_url or os.environ.get(
            "RAG_DOCUMENTS_URL",
            "https://api.github.com/repos/nambili-samuel/eva-knowledge/contents/documents"
        )
        
        self.documents = []  # List of processed documents
        self.document_chunks = []  # Chunks for better retrieval
        self.last_sync = None
        self.sync_interval = timedelta(hours=1)  # Re-sync every hour
        
        # Cache directory
        self.cache_dir = "/tmp/rag_cache"
        os.makedirs(self.cache_dir, exist_ok=True)
        
        logger.info(f"📚 RAG System initialized")
        logger.info(f"📁 Document source: {self.github_repo_url}")
    
    async def sync_documents(self):
        """Sync documents from GitHub repository"""
        try:
            logger.info("📥 Syncing documents from GitHub...")
            
            async with aiohttp.ClientSession() as session:
                # Get list of files from GitHub API
                async with session.get(self.github_repo_url, timeout=30) as response:
                    if response.status != 200:
                        logger.error(f"❌ Failed to fetch document list: {response.status}")
                        return False
                    
                    files = await response.json()
                    
                    if not isinstance(files, list):
                        logger.error("❌ Invalid response from GitHub API")
                        return False
                    
                    # Process each file
                    new_docs = 0
                    updated_docs = 0
                    
                    for file_info in files:
                        if not isinstance(file_info, dict):
                            continue
                        
                        file_name = file_info.get('name', '')
                        download_url = file_info.get('download_url')
                        
                        if not download_url:
                            continue
                        
                        # Only process supported file types
                        if not self._is_supported_file(file_name):
                            continue
                        
                        # Download and process document
                        success = await self._download_and_process(
                            session, file_name, download_url
                        )
                        
                        if success:
                            # Check if new or updated
                            if self._is_new_document(file_name):
                                new_docs += 1
                            else:
                                updated_docs += 1
                    
                    self.last_sync = datetime.now()
                    logger.info(f"✅ Document sync complete: {new_docs} new, {updated_docs} updated")
                    logger.info(f"📚 Total documents: {len(self.documents)}")
                    logger.info(f"🔍 Total searchable chunks: {len(self.document_chunks)}")
                    
                    return True
        
        except Exception as e:
            logger.error(f"❌ Document sync error: {e}")
            return False
    
    def _is_supported_file(self, filename: str) -> bool:
        """Check if file type is supported"""
        supported_extensions = ['.pdf', '.docx', '.doc', '.txt', '.md']
        return any(filename.lower().endswith(ext) for ext in supported_extensions)
    
    def _is_new_document(self, filename: str) -> bool:
        """Check if document is new (not in current collection)"""
        return not any(doc['filename'] == filename for doc in self.documents)
    
    async def _download_and_process(self, session, filename: str, url: str) -> bool:
        """Download and process a document"""
        try:
            # Download file
            async with session.get(url, timeout=60) as response:
                if response.status != 200:
                    logger.warning(f"⚠️ Failed to download {filename}: {response.status}")
                    return False
                
                content = await response.read()
                
                # Save to cache
                cache_path = os.path.join(self.cache_dir, filename)
                with open(cache_path, 'wb') as f:
                    f.write(content)
                
                # Process based on file type
                text_content = await self._extract_text(cache_path, filename)
                
                if not text_content:
                    logger.warning(f"⚠️ No text extracted from {filename}")
                    return False
                
                # Create document metadata
                doc_hash = hashlib.md5(content).hexdigest()
                
                document = {
                    'filename': filename,
                    'content': text_content,
                    'hash': doc_hash,
                    'url': url,
                    'processed_at': datetime.now().isoformat(),
                    'word_count': len(text_content.split()),
                    'char_count': len(text_content)
                }
                
                # Remove old version if exists
                self.documents = [d for d in self.documents if d['filename'] != filename]
                
                # Add new document
                self.documents.append(document)
                
                # Create searchable chunks
                chunks = self._create_chunks(text_content, filename)
                
                # Remove old chunks for this document
                self.document_chunks = [
                    c for c in self.document_chunks 
                    if c['filename'] != filename
                ]
                
                # Add new chunks
                self.document_chunks.extend(chunks)
                
                logger.info(f"✅ Processed {filename}: {len(chunks)} chunks, {document['word_count']} words")
                
                return True
        
        except Exception as e:
            logger.error(f"❌ Error processing {filename}: {e}")
            return False
    
    async def _extract_text(self, file_path: str, filename: str) -> str:
        """Extract text from various file formats"""
        try:
            # Text files
            if filename.endswith('.txt') or filename.endswith('.md'):
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
            
            # PDF files
            elif filename.endswith('.pdf'):
                return await self._extract_pdf(file_path)
            
            # Word documents
            elif filename.endswith('.docx') or filename.endswith('.doc'):
                return await self._extract_docx(file_path)
            
            return ""
        
        except Exception as e:
            logger.error(f"❌ Text extraction error for {filename}: {e}")
            return ""
    
    async def _extract_pdf(self, file_path: str) -> str:
        """Extract text from PDF using PyPDF2"""
        try:
            # Try importing PyPDF2
            try:
                from PyPDF2 import PdfReader
            except ImportError:
                logger.warning("⚠️ PyPDF2 not installed, cannot process PDFs")
                return ""
            
            text = ""
            reader = PdfReader(file_path)
            
            for page in reader.pages:
                text += page.extract_text() + "\n\n"
            
            return text.strip()
        
        except Exception as e:
            logger.error(f"❌ PDF extraction error: {e}")
            return ""
    
    async def _extract_docx(self, file_path: str) -> str:
        """Extract text from DOCX using python-docx"""
        try:
            # Try importing python-docx
            try:
                from docx import Document
            except ImportError:
                logger.warning("⚠️ python-docx not installed, cannot process DOCX files")
                return ""
            
            doc = Document(file_path)
            text = ""
            
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            
            return text.strip()
        
        except Exception as e:
            logger.error(f"❌ DOCX extraction error: {e}")
            return ""
    
    def _create_chunks(self, text: str, filename: str, chunk_size: int = 500) -> List[Dict]:
        """
        Split document into searchable chunks
        
        Args:
            text: Document text
            filename: Source filename
            chunk_size: Words per chunk
        
        Returns:
            List of chunk dictionaries
        """
        # Clean text
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Split into sentences (basic)
        sentences = re.split(r'[.!?]+', text)
        
        chunks = []
        current_chunk = []
        current_word_count = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            words = sentence.split()
            
            # If adding this sentence exceeds chunk size, save current chunk
            if current_word_count + len(words) > chunk_size and current_chunk:
                chunk_text = ' '.join(current_chunk)
                
                chunks.append({
                    'text': chunk_text,
                    'filename': filename,
                    'word_count': current_word_count,
                    'keywords': self._extract_keywords(chunk_text)
                })
                
                current_chunk = []
                current_word_count = 0
            
            current_chunk.append(sentence)
            current_word_count += len(words)
        
        # Add remaining chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunks.append({
                'text': chunk_text,
                'filename': filename,
                'word_count': current_word_count,
                'keywords': self._extract_keywords(chunk_text)
            })
        
        return chunks
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text for better search"""
        # Convert to lowercase
        text_lower = text.lower()
        
        # Remove common words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those'
        }
        
        # Extract words
        words = re.findall(r'\b[a-z]{3,}\b', text_lower)
        
        # Filter stop words
        keywords = [w for w in words if w not in stop_words]
        
        # Get unique keywords (keep top 20)
        unique_keywords = []
        seen = set()
        
        for word in keywords:
            if word not in seen and len(unique_keywords) < 20:
                unique_keywords.append(word)
                seen.add(word)
        
        return unique_keywords
    
    def search_documents(self, query: str, limit: int = 5) -> List[Dict]:
        """
        Search documents using RAG
        
        Args:
            query: Search query
            limit: Maximum results
        
        Returns:
            List of relevant chunks with metadata
        """
        if not self.document_chunks:
            return []
        
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        # Score each chunk
        scored_chunks = []
        
        for chunk in self.document_chunks:
            score = 0
            chunk_text_lower = chunk['text'].lower()
            
            # Exact phrase match (highest score)
            if query_lower in chunk_text_lower:
                score += 100
            
            # Word matches
            chunk_words = set(chunk_text_lower.split())
            matching_words = query_words.intersection(chunk_words)
            score += len(matching_words) * 10
            
            # Keyword matches
            matching_keywords = set(chunk.get('keywords', [])).intersection(query_words)
            score += len(matching_keywords) * 5
            
            # Proximity bonus (words appear close together)
            for word in query_words:
                if word in chunk_text_lower:
                    score += 2
            
            if score > 0:
                scored_chunks.append({
                    'chunk': chunk,
                    'score': score
                })
        
        # Sort by score
        scored_chunks.sort(key=lambda x: x['score'], reverse=True)
        
        # Return top results
        results = []
        for item in scored_chunks[:limit]:
            chunk = item['chunk']
            results.append({
                'text': chunk['text'],
                'filename': chunk['filename'],
                'score': item['score'],
                'source': 'RAG Document',
                'type': 'document_chunk'
            })
        
        return results
    
    def get_document_summary(self, filename: str) -> Optional[Dict]:
        """Get summary of a specific document"""
        for doc in self.documents:
            if doc['filename'] == filename:
                # Create summary
                content_preview = doc['content'][:500] + "..." if len(doc['content']) > 500 else doc['content']
                
                return {
                    'filename': doc['filename'],
                    'word_count': doc['word_count'],
                    'char_count': doc['char_count'],
                    'preview': content_preview,
                    'processed_at': doc['processed_at']
                }
        
        return None
    
    def list_documents(self) -> List[Dict]:
        """List all available documents"""
        return [
            {
                'filename': doc['filename'],
                'word_count': doc['word_count'],
                'processed_at': doc['processed_at']
            }
            for doc in self.documents
        ]
    
    async def auto_sync(self):
        """Auto-sync documents periodically"""
        while True:
            try:
                # Check if sync needed
                if not self.last_sync or datetime.now() - self.last_sync > self.sync_interval:
                    await self.sync_documents()
                
                # Wait 10 minutes before checking again
                await asyncio.sleep(600)
            
            except Exception as e:
                logger.error(f"❌ Auto-sync error: {e}")
                await asyncio.sleep(600)
    
    def should_sync(self) -> bool:
        """Check if documents should be synced"""
        if not self.last_sync:
            return True
        
        return datetime.now() - self.last_sync > self.sync_interval
    
    def get_stats(self) -> Dict:
        """Get RAG system statistics"""
        return {
            'total_documents': len(self.documents),
            'total_chunks': len(self.document_chunks),
            'last_sync': self.last_sync.isoformat() if self.last_sync else 'Never',
            'cache_dir': self.cache_dir,
            'source_url': self.github_repo_url
        }

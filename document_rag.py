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
                           Format: https://api.github.com/repos/username/repo/contents/documents
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
    
    def _create_chunks(self, text: str, filename: str, chunk_size: int = 300) -> List[Dict]:
        """
        Split document into SMART searchable chunks
        
        Args:
            text: Document text
            filename: Source filename
            chunk_size: Words per chunk (reduced for conciseness)
        
        Returns:
            List of chunk dictionaries
        """
        # Clean text
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Better sentence splitting (preserves meaning)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        chunks = []
        current_chunk = []
        current_word_count = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence or len(sentence.split()) < 3:
                continue
            
            words = sentence.split()
            
            # Create topic-based chunks
            # Look for headings or new topics
            is_heading = (
                sentence.isupper() or 
                len(sentence) < 50 or
                re.match(r'^[A-Z][a-z]*(?:\s+[A-Z][a-z]*)*:$', sentence) or
                re.match(r'^[0-9]+\.\s', sentence)
            )
            
            # If we have a heading or starting new topic, save current chunk
            if is_heading and current_chunk:
                chunk_text = ' '.join(current_chunk)
                if current_word_count >= 50:  # Minimum chunk size
                    chunks.append({
                        'text': chunk_text,
                        'filename': filename,
                        'word_count': current_word_count,
                        'keywords': self._extract_keywords(chunk_text),
                        'is_summary': False
                    })
                current_chunk = []
                current_word_count = 0
            
            # Add sentence to chunk
            current_chunk.append(sentence)
            current_word_count += len(words)
            
            # If chunk reaches size limit, save it
            if current_word_count >= chunk_size:
                chunk_text = ' '.join(current_chunk)
                chunks.append({
                    'text': chunk_text,
                    'filename': filename,
                    'word_count': current_word_count,
                    'keywords': self._extract_keywords(chunk_text),
                    'is_summary': False
                })
                current_chunk = []
                current_word_count = 0
        
        # Add remaining chunk
        if current_chunk and current_word_count >= 30:
            chunk_text = ' '.join(current_chunk)
            chunks.append({
                'text': chunk_text,
                'filename': filename,
                'word_count': current_word_count,
                'keywords': self._extract_keywords(chunk_text),
                'is_summary': False
            })
        
        # Create summary chunks for each document
        if chunks:
            # Extract first 2-3 chunks as summary
            summary_text = ' '.join([chunk['text'] for chunk in chunks[:3]])
            if len(summary_text) > 500:
                summary_text = summary_text[:497] + "..."
            
            # Insert summary as first chunk
            chunks.insert(0, {
                'text': summary_text,
                'filename': filename,
                'word_count': len(summary_text.split()),
                'keywords': self._extract_keywords(summary_text),
                'is_summary': True
            })
        
        return chunks
    
    def _summarize_chunk(self, chunk_text: str, query: str = None) -> str:
        """
        Create concise summary of chunk based on query
        """
        if not query or len(chunk_text) < 200:
            # Return the chunk as-is if short or no query
            if len(chunk_text) > 400:
                return self._smart_truncate(chunk_text, 400, query)
            return chunk_text
        
        # Look for sentences that contain query words
        sentences = re.split(r'(?<=[.!?])\s+', chunk_text)
        query_words = query.lower().split()
        
        # Remove common stop words from query
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those',
            'what', 'where', 'when', 'why', 'how', 'who', 'which', 'tell', 'me',
            'about', 'know', 'please'
        }
        query_words = [w for w in query_words if w not in stop_words]
        
        relevant_sentences = []
        for sentence in sentences:
            sentence_lower = sentence.lower()
            # Score sentence relevance
            score = sum(1 for word in query_words if word in sentence_lower)
            if score > 0:
                relevant_sentences.append((score, sentence))
        
        # If we found relevant sentences, use them
        if relevant_sentences:
            # Sort by relevance score
            relevant_sentences.sort(key=lambda x: x[0], reverse=True)
            summary = ' '.join([sentence for _, sentence in relevant_sentences[:3]])  # Max 3 sentences
            if len(summary) > 400:
                summary = self._smart_truncate(summary, 400, query)
            return summary
        
        # Fallback: first 2-3 sentences
        summary = ' '.join(sentences[:3])
        if len(summary) > 400:
            summary = self._smart_truncate(summary, 400, query)
        return summary
    
    def _smart_truncate(self, text: str, max_length: int = 400, query: str = None) -> str:
        """
        Smart truncation that preserves sentences and relevance
        """
        if len(text) <= max_length:
            return text
        
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        # If query provided, find most relevant sentences
        if query:
            query_words = query.lower().split()
            # Remove stop words
            stop_words = {
                'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
                'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
                'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those',
                'what', 'where', 'when', 'why', 'how', 'who', 'which', 'tell', 'me',
                'about', 'know', 'please'
            }
            query_words = [w for w in query_words if w not in stop_words]
            
            sentence_scores = []
            
            for i, sentence in enumerate(sentences):
                score = 0
                sentence_lower = sentence.lower()
                for word in query_words:
                    if word in sentence_lower:
                        score += 1
                sentence_scores.append((i, score, sentence))
            
            # Sort by relevance
            sentence_scores.sort(key=lambda x: x[1], reverse=True)
            
            # Build from most relevant sentences
            result = []
            total_length = 0
            
            for i, score, sentence in sentence_scores:
                if score > 0 and total_length + len(sentence) < max_length - 100:  # Leave room
                    result.append(sentence)
                    total_length += len(sentence)
            
            if result:
                truncated = ' '.join(result)
                if len(truncated) > max_length:
                    truncated = truncated[:max_length-3] + "..."
                return truncated
        
        # Fallback: take first sentences until limit
        result = []
        total_length = 0
        
        for sentence in sentences:
            if total_length + len(sentence) < max_length - 50:  # Leave room for "..."
                result.append(sentence)
                total_length += len(sentence)
            else:
                break
        
        if result:
            truncated = ' '.join(result)
            if len(truncated) < len(text):
                truncated += "..."
            return truncated
        
        # Final fallback
        return text[:max_length-3] + "..."
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text for better search"""
        # Convert to lowercase
        text_lower = text.lower()
        
        # Remove common words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those',
            'what', 'where', 'when', 'why', 'how', 'who', 'which', 'tell', 'me',
            'about', 'know', 'please'
        }
        
        # Extract words
        words = re.findall(r'\b[a-z]{3,}\b', text_lower)
        
        # Filter stop words
        keywords = [w for w in words if w not in stop_words]
        
        # Get unique keywords (keep top 15)
        unique_keywords = []
        seen = set()
        
        for word in keywords:
            if word not in seen and len(unique_keywords) < 15:
                unique_keywords.append(word)
                seen.add(word)
        
        return unique_keywords
    
    def search_documents(self, query: str, limit: int = 2) -> List[Dict]:
        """
        Search documents using RAG with improved relevance scoring
        
        Args:
            query: Search query
            limit: Maximum results
        
        Returns:
            List of relevant chunks with metadata
        """
        if not self.document_chunks:
            return []
        
        query_lower = query.lower().strip()
        
        # Extract meaningful words from query
        query_words = re.findall(r'\b[a-z]{3,}\b', query_lower)
        
        # Remove common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those',
            'what', 'where', 'when', 'why', 'how', 'who', 'which', 'tell', 'me',
            'about', 'know', 'please', 'could', 'would', 'thank', 'thanks',
            'hello', 'hi', 'hey', 'eva', 'bot', 'namibia', 'namibian'
        }
        query_words = [w for w in query_words if w not in stop_words]
        
        if not query_words:
            return []
        
        scored_chunks = []
        
        for chunk in self.document_chunks:
            score = 0
            chunk_text_lower = chunk['text'].lower()
            
            # 1. Exact phrase match (highest priority)
            if query_lower in chunk_text_lower:
                score += 1000
            
            # 2. All query words appear
            all_words_match = all(word in chunk_text_lower for word in query_words)
            if all_words_match and query_words:
                score += 500
            
            # 3. Most query words appear
            matching_words = sum(1 for word in query_words if word in chunk_text_lower)
            if matching_words > 0:
                score += matching_words * 100
                percentage_match = matching_words / len(query_words)
                score += int(percentage_match * 200)
            
            # 4. Proximity bonus - words appear close together
            chunk_words = chunk_text_lower.split()
            for i in range(len(chunk_words) - len(query_words) + 1):
                window = chunk_words[i:i + len(query_words)]
                window_matches = sum(1 for word in query_words if word in window)
                if window_matches == len(query_words):
                    score += 300
                    break
            
            # 5. Prefer summary chunks for overview
            if chunk.get('is_summary'):
                score += 150
            
            # 6. Prefer shorter, more concise chunks
            word_count = len(chunk_text_lower.split())
            if word_count < 100:
                score += 50
            elif word_count > 300:
                score -= 30
            
            # 7. Question word matching
            question_words = ['who', 'what', 'where', 'when', 'why', 'how', 'which']
            for q_word in question_words:
                if q_word in query_lower and q_word in chunk_text_lower:
                    score += 50
            
            # 8. Remove headings penalty (avoid "WELCOME TO" headings)
            if chunk_text_lower.startswith('welcome to') or chunk_text_lower.isupper():
                score -= 100
            
            if score > 0:
                scored_chunks.append({
                    'chunk': chunk,
                    'score': score,
                    'matching_words': matching_words
                })
        
        # Sort by score
        scored_chunks.sort(key=lambda x: x['score'], reverse=True)
        
        # Get top results and summarize
        results = []
        for item in scored_chunks[:limit]:
            chunk = item['chunk']
            
            # Summarize chunk based on query
            summarized_text = self._summarize_chunk(chunk['text'], query)
            
            # Clean up the text - remove headings
            lines = summarized_text.split('\n')
            clean_lines = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith('WELCOME') and not line.isupper():
                    clean_lines.append(line)
            
            summarized_text = '\n'.join(clean_lines)
            
            # Ensure we don't return too much text
            if len(summarized_text) > 500:
                summarized_text = self._smart_truncate(summarized_text, 500, query)
            
            # Remove document headings
            summarized_text = re.sub(r'^WELCOME TO.*?\n', '', summarized_text, flags=re.IGNORECASE)
            summarized_text = re.sub(r'^INTRODUCTION.*?\n', '', summarized_text, flags=re.IGNORECASE)
            summarized_text = summarized_text.strip()
            
            results.append({
                'text': summarized_text,
                'filename': chunk['filename'],
                'score': item['score'],
                'source': 'document',
                'type': 'document_chunk',
                'is_summary': chunk.get('is_summary', False),
                'original_length': len(chunk['text']),
                'summarized_length': len(summarized_text)
            })
        
        return results
    
    def get_document_summary(self, filename: str) -> Optional[Dict]:
        """Get summary of a specific document"""
        for doc in self.documents:
            if doc['filename'] == filename:
                # Create summary
                content_preview = doc['content'][:300] + "..." if len(doc['content']) > 300 else doc['content']
                
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

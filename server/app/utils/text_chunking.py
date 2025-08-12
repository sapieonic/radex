import re
from typing import List, Dict, Any

def chunk_text(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 200,
    preserve_sentences: bool = True
) -> List[str]:
    """
    Split text into overlapping chunks
    
    Args:
        text: Text to chunk
        chunk_size: Maximum size of each chunk
        overlap: Number of characters to overlap between chunks
        preserve_sentences: Whether to try to preserve sentence boundaries
    
    Returns:
        List of text chunks
    """
    if not text.strip():
        return []
    
    if preserve_sentences:
        return chunk_text_by_sentences(text, chunk_size, overlap)
    else:
        return chunk_text_simple(text, chunk_size, overlap)

def chunk_text_simple(text: str, chunk_size: int, overlap: int) -> List[str]:
    """Simple chunking that splits at character boundaries"""
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        
        if chunk.strip():
            chunks.append(chunk.strip())
        
        start = end - overlap
        if start >= len(text):
            break
    
    return chunks

def chunk_text_by_sentences(text: str, chunk_size: int, overlap: int) -> List[str]:
    """Chunk text while trying to preserve sentence boundaries"""
    # Split into sentences using regex
    sentence_pattern = r'(?<=[.!?])\s+'
    sentences = re.split(sentence_pattern, text)
    
    chunks = []
    current_chunk = ""
    current_size = 0
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        
        sentence_size = len(sentence)
        
        # If this sentence alone is larger than chunk_size, split it
        if sentence_size > chunk_size:
            # Add current chunk if it exists
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = ""
                current_size = 0
            
            # Split the large sentence
            sentence_chunks = chunk_text_simple(sentence, chunk_size, overlap)
            chunks.extend(sentence_chunks)
            continue
        
        # If adding this sentence would exceed chunk_size, finalize current chunk
        if current_size + sentence_size > chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            
            # Start new chunk with overlap from the end of the previous chunk
            overlap_text = get_overlap_text(current_chunk, overlap)
            current_chunk = overlap_text + " " + sentence if overlap_text else sentence
            current_size = len(current_chunk)
        else:
            # Add sentence to current chunk
            if current_chunk:
                current_chunk += " " + sentence
            else:
                current_chunk = sentence
            current_size = len(current_chunk)
    
    # Add the last chunk if it exists
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    return chunks

def get_overlap_text(text: str, overlap_size: int) -> str:
    """Get overlap text from the end of a chunk"""
    if len(text) <= overlap_size:
        return text
    
    # Try to find a good break point (word boundary)
    overlap_text = text[-overlap_size:]
    
    # Find the first space to avoid cutting words
    space_index = overlap_text.find(' ')
    if space_index > 0:
        overlap_text = overlap_text[space_index + 1:]
    
    return overlap_text

def chunk_text_with_metadata(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 200,
    document_id: str = None,
    document_title: str = None
) -> List[Dict[str, Any]]:
    """
    Chunk text and return with metadata
    
    Returns:
        List of dictionaries with 'text' and 'metadata' keys
    """
    chunks = chunk_text(text, chunk_size, overlap)
    
    result = []
    for i, chunk in enumerate(chunks):
        metadata = {
            "chunk_index": i,
            "chunk_size": len(chunk),
            "total_chunks": len(chunks)
        }
        
        if document_id:
            metadata["document_id"] = document_id
        
        if document_title:
            metadata["document_title"] = document_title
        
        result.append({
            "text": chunk,
            "metadata": metadata
        })
    
    return result

def estimate_tokens(text: str) -> int:
    """Rough estimation of token count (assuming ~4 characters per token)"""
    return len(text) // 4

def chunk_text_by_tokens(
    text: str,
    max_tokens: int = 250,
    overlap_tokens: int = 50
) -> List[str]:
    """Chunk text based on estimated token count"""
    max_chars = max_tokens * 4
    overlap_chars = overlap_tokens * 4
    
    return chunk_text(text, max_chars, overlap_chars)
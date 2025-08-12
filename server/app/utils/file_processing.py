import os
import mimetypes
from typing import Optional
from pathlib import Path
import pypdf
import docx
from bs4 import BeautifulSoup
import markdown

def get_file_type(filename: str) -> Optional[str]:
    """Get file type from filename"""
    _, ext = os.path.splitext(filename.lower())
    return ext.lstrip('.') if ext else None

def is_supported_file_type(file_type: str) -> bool:
    """Check if file type is supported for text extraction"""
    supported_types = ['pdf', 'docx', 'doc', 'txt', 'md', 'html', 'htm']
    return file_type.lower() in supported_types

def extract_text_from_file(file_path: str, file_type: str) -> str:
    """Extract text from various file formats"""
    file_type = file_type.lower()
    
    try:
        if file_type == 'pdf':
            return extract_pdf_text(file_path)
        elif file_type in ['docx', 'doc']:
            return extract_docx_text(file_path)
        elif file_type in ['html', 'htm']:
            return extract_html_text(file_path)
        elif file_type == 'md':
            return extract_markdown_text(file_path)
        elif file_type == 'txt':
            return extract_text_file(file_path)
        else:
            # Try to read as plain text
            return extract_text_file(file_path)
    except Exception as e:
        raise ValueError(f"Error extracting text from {file_type} file: {str(e)}")

def extract_pdf_text(file_path: str) -> str:
    """Extract text from PDF file"""
    text = ""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = pypdf.PdfReader(file)
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        raise ValueError(f"Error reading PDF file: {str(e)}")
    
    return text.strip()

def extract_docx_text(file_path: str) -> str:
    """Extract text from DOCX file"""
    try:
        doc = docx.Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text.strip()
    except Exception as e:
        raise ValueError(f"Error reading DOCX file: {str(e)}")

def extract_html_text(file_path: str) -> str:
    """Extract text from HTML file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        text = soup.get_text()
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text
    except Exception as e:
        raise ValueError(f"Error reading HTML file: {str(e)}")

def extract_markdown_text(file_path: str) -> str:
    """Extract text from Markdown file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Convert markdown to HTML then extract text
        html = markdown.markdown(content)
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text()
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        text = '\n'.join(line for line in lines if line)
        
        return text
    except Exception as e:
        raise ValueError(f"Error reading Markdown file: {str(e)}")

def extract_text_file(file_path: str) -> str:
    """Extract text from plain text file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except UnicodeDecodeError:
        # Try different encodings
        encodings = ['latin-1', 'cp1252', 'iso-8859-1']
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as file:
                    return file.read()
            except UnicodeDecodeError:
                continue
        raise ValueError("Could not decode text file with any supported encoding")
    except Exception as e:
        raise ValueError(f"Error reading text file: {str(e)}")

def get_file_mime_type(file_path: str) -> Optional[str]:
    """Get MIME type of file"""
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type

def validate_file_size(file_size: int, max_size_mb: int = 50) -> bool:
    """Validate file size (default max 50MB)"""
    max_size_bytes = max_size_mb * 1024 * 1024
    return file_size <= max_size_bytes
import re
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from bs4 import BeautifulSoup
from markdownify import markdownify as md
import logging

logger = logging.getLogger(__name__)


class ConfluenceExtractor:
    """Extract and transform content from Confluence pages"""
    
    def __init__(self):
        self.macro_handlers = {
            'code': self._handle_code_macro,
            'panel': self._handle_panel_macro,
            'info': self._handle_info_macro,
            'warning': self._handle_warning_macro,
            'note': self._handle_note_macro,
            'tip': self._handle_tip_macro,
            'toc': self._handle_toc_macro,
            'excerpt': self._handle_excerpt_macro,
        }
    
    def extract_page_content(self, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract content and metadata from a Confluence page"""
        
        # Extract basic metadata
        metadata = {
            'page_id': page_data.get('id'),
            'title': page_data.get('title', 'Untitled'),
            'space_key': page_data.get('space', {}).get('key'),
            'space_name': page_data.get('space', {}).get('name'),
            'version': page_data.get('version', {}).get('number'),
            'created_by': page_data.get('version', {}).get('by', {}).get('email'),
            'created_date': page_data.get('history', {}).get('createdDate'),
            'modified_date': page_data.get('version', {}).get('when'),
            'url': page_data.get('_links', {}).get('webui'),
            'parent_id': None,
            'labels': []
        }
        
        # Extract parent information
        ancestors = page_data.get('ancestors', [])
        if ancestors:
            metadata['parent_id'] = ancestors[-1].get('id')
        
        # Extract labels
        if 'metadata' in page_data and 'labels' in page_data['metadata']:
            labels = page_data['metadata']['labels'].get('results', [])
            metadata['labels'] = [label.get('name') for label in labels]
        
        # Extract and convert content
        body_storage = page_data.get('body', {}).get('storage', {}).get('value', '')
        
        # Process Confluence storage format
        processed_html = self._process_confluence_html(body_storage)
        
        # Convert to markdown
        markdown_content = self._html_to_markdown(processed_html)
        
        # Clean up markdown
        markdown_content = self._clean_markdown(markdown_content)
        
        # Generate content hash for change detection
        content_hash = hashlib.sha256(markdown_content.encode()).hexdigest()
        
        return {
            'content': markdown_content,
            'metadata': metadata,
            'content_hash': content_hash,
            'has_attachments': self._check_attachments(page_data)
        }
    
    def _process_confluence_html(self, html_content: str) -> str:
        """Process Confluence storage format HTML"""
        if not html_content:
            return ""
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Process Confluence macros
        for macro in soup.find_all('ac:structured-macro'):
            macro_name = macro.get('ac:name', '')
            if macro_name in self.macro_handlers:
                replacement = self.macro_handlers[macro_name](macro)
                if replacement:
                    macro.replace_with(replacement)
            else:
                # Handle unknown macros generically
                self._handle_generic_macro(macro)
        
        # Process Confluence-specific elements
        self._process_confluence_links(soup)
        self._process_confluence_images(soup)
        self._process_confluence_tables(soup)
        
        return str(soup)
    
    def _html_to_markdown(self, html_content: str) -> str:
        """Convert HTML to Markdown"""
        if not html_content:
            return ""
        
        # Configure markdownify
        markdown = md(
            html_content,
            heading_style="ATX",
            bullets="-*+",
            code_language="",
            strip=['span', 'div'],
            wrap_width=0  # Don't wrap lines
        )
        
        return markdown
    
    def _clean_markdown(self, markdown_content: str) -> str:
        """Clean up converted markdown"""
        if not markdown_content:
            return ""
        
        # Remove excessive blank lines
        markdown_content = re.sub(r'\n\n\n+', '\n\n', markdown_content)
        
        # Fix broken markdown links
        markdown_content = re.sub(r'\[([^\]]+)\]\s+\(([^)]+)\)', r'[\1](\2)', markdown_content)
        
        # Clean up code blocks
        markdown_content = re.sub(r'```\n\n', '```\n', markdown_content)
        markdown_content = re.sub(r'\n\n```', '\n```', markdown_content)
        
        # Remove trailing whitespace
        lines = markdown_content.split('\n')
        lines = [line.rstrip() for line in lines]
        markdown_content = '\n'.join(lines)
        
        return markdown_content.strip()
    
    def _handle_code_macro(self, macro) -> BeautifulSoup:
        """Handle Confluence code macro"""
        code_content = macro.find('ac:plain-text-body')
        if code_content:
            # Get language if specified
            language = ''
            for param in macro.find_all('ac:parameter'):
                if param.get('ac:name') == 'language':
                    language = param.text
                    break
            
            # Create a code block
            pre = BeautifulSoup(f'<pre><code class="language-{language}">{code_content.text}</code></pre>', 'html.parser')
            return pre
        return None
    
    def _handle_panel_macro(self, macro) -> BeautifulSoup:
        """Handle Confluence panel macro"""
        title = ''
        for param in macro.find_all('ac:parameter'):
            if param.get('ac:name') == 'title':
                title = param.text
                break
        
        body = macro.find('ac:rich-text-body')
        if body:
            # Create a blockquote with title
            content = f'<blockquote><strong>{title}</strong><br/>{body.decode_contents()}</blockquote>'
            return BeautifulSoup(content, 'html.parser')
        return None
    
    def _handle_info_macro(self, macro) -> BeautifulSoup:
        """Handle info macro"""
        return self._handle_admonition_macro(macro, 'ℹ️ INFO')
    
    def _handle_warning_macro(self, macro) -> BeautifulSoup:
        """Handle warning macro"""
        return self._handle_admonition_macro(macro, '⚠️ WARNING')
    
    def _handle_note_macro(self, macro) -> BeautifulSoup:
        """Handle note macro"""
        return self._handle_admonition_macro(macro, '📝 NOTE')
    
    def _handle_tip_macro(self, macro) -> BeautifulSoup:
        """Handle tip macro"""
        return self._handle_admonition_macro(macro, '💡 TIP')
    
    def _handle_admonition_macro(self, macro, prefix: str) -> BeautifulSoup:
        """Generic handler for admonition-style macros"""
        body = macro.find('ac:rich-text-body')
        if body:
            content = f'<blockquote><strong>{prefix}:</strong><br/>{body.decode_contents()}</blockquote>'
            return BeautifulSoup(content, 'html.parser')
        return None
    
    def _handle_toc_macro(self, macro) -> BeautifulSoup:
        """Handle table of contents macro"""
        # Replace with a placeholder
        return BeautifulSoup('<p>[Table of Contents]</p>', 'html.parser')
    
    def _handle_excerpt_macro(self, macro) -> BeautifulSoup:
        """Handle excerpt macro"""
        body = macro.find('ac:rich-text-body')
        if body:
            content = f'<blockquote><em>{body.decode_contents()}</em></blockquote>'
            return BeautifulSoup(content, 'html.parser')
        return None
    
    def _handle_generic_macro(self, macro):
        """Handle unknown macros"""
        # Extract macro content and replace with placeholder
        macro_name = macro.get('ac:name', 'unknown')
        body = macro.find('ac:rich-text-body') or macro.find('ac:plain-text-body')
        
        if body:
            replacement = BeautifulSoup(f'<div>[{macro_name.upper()} MACRO: {body.text}]</div>', 'html.parser')
            macro.replace_with(replacement)
        else:
            macro.decompose()
    
    def _process_confluence_links(self, soup: BeautifulSoup):
        """Process Confluence-specific links"""
        # Process user mentions
        for link in soup.find_all('ac:link'):
            user = link.find('ri:user')
            if user:
                username = user.get('ri:username', 'unknown')
                link.replace_with(f'@{username}')
            
            # Process page links
            page = link.find('ri:page')
            if page:
                title = page.get('ri:content-title', 'Page')
                link.replace_with(f'[[{title}]]')
    
    def _process_confluence_images(self, soup: BeautifulSoup):
        """Process Confluence images"""
        for image in soup.find_all('ac:image'):
            attachment = image.find('ri:attachment')
            if attachment:
                filename = attachment.get('ri:filename', 'image')
                alt_text = image.get('ac:alt', filename)
                image.replace_with(f'![{alt_text}]({filename})')
    
    def _process_confluence_tables(self, soup: BeautifulSoup):
        """Ensure tables are properly formatted"""
        # Tables should be handled by markdownify, but we can enhance them here if needed
        for table in soup.find_all('table'):
            # Add a class to help markdownify
            table['class'] = table.get('class', []) + ['confluence-table']
    
    def _check_attachments(self, page_data: Dict[str, Any]) -> bool:
        """Check if page has attachments"""
        children = page_data.get('children', {})
        attachments = children.get('attachment', {})
        return attachments.get('size', 0) > 0
    
    def extract_attachment_info(self, attachment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract attachment metadata"""
        return {
            'id': attachment_data.get('id'),
            'title': attachment_data.get('title'),
            'filename': attachment_data.get('title'),  # Usually the same
            'media_type': attachment_data.get('metadata', {}).get('mediaType'),
            'file_size': attachment_data.get('extensions', {}).get('fileSize'),
            'created_date': attachment_data.get('history', {}).get('createdDate'),
            'download_url': attachment_data.get('_links', {}).get('download'),
            'version': attachment_data.get('version', {}).get('number')
        }
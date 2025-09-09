import time
import requests
from typing import Optional, Dict, Any, List
from urllib.parse import urljoin, quote
import logging

from app.models import ConfluenceCredential, ConfluenceType
from app.core.exceptions import BadRequestException, NotFoundException
from app.services.confluence.auth_service import ConfluenceAuthService

logger = logging.getLogger(__name__)


class ConfluenceClient:
    """Client for interacting with Confluence API"""
    
    def __init__(self, credential: ConfluenceCredential, auth_service: ConfluenceAuthService):
        self.credential = credential
        self.auth_service = auth_service
        self.base_url = credential.base_url.rstrip('/')
        self.session = self._create_session()
        self._setup_authentication()
        
    def _create_session(self) -> requests.Session:
        """Create a requests session with retry logic"""
        session = requests.Session()
        session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        return session
    
    def _setup_authentication(self):
        """Setup authentication based on Confluence type"""
        tokens = self.auth_service.get_decrypted_tokens(self.credential)
        
        if self.credential.confluence_type == ConfluenceType.CLOUD:
            # Use OAuth for Cloud
            if tokens['oauth_token']:
                self.session.headers['Authorization'] = f"Bearer {tokens['oauth_token']}"
            elif tokens['api_token'] and self.credential.email:
                # Fallback to API token for Cloud
                import base64
                auth_string = f"{self.credential.email}:{tokens['api_token']}"
                encoded_auth = base64.b64encode(auth_string.encode()).decode()
                self.session.headers['Authorization'] = f"Basic {encoded_auth}"
        else:
            # Use API token for Server/Data Center
            if tokens['api_token'] and self.credential.email:
                import base64
                auth_string = f"{self.credential.email}:{tokens['api_token']}"
                encoded_auth = base64.b64encode(auth_string.encode()).decode()
                self.session.headers['Authorization'] = f"Basic {encoded_auth}"
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        retry_count: int = 3,
        backoff_factor: float = 1.0
    ) -> Dict[str, Any]:
        """Make an API request with retry logic and rate limiting"""
        url = urljoin(self.base_url, endpoint)
        
        for attempt in range(retry_count):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=data
                )
                
                if response.status_code == 429:  # Rate limited
                    retry_after = int(response.headers.get('Retry-After', 60))
                    logger.warning(f"Rate limited. Waiting {retry_after} seconds.")
                    time.sleep(retry_after)
                    continue
                    
                response.raise_for_status()
                return response.json() if response.text else {}
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 401:
                    raise BadRequestException("Authentication failed. Please check your credentials.")
                elif e.response.status_code == 403:
                    raise BadRequestException("Permission denied. Check your Confluence permissions.")
                elif e.response.status_code == 404:
                    raise NotFoundException(f"Resource not found: {endpoint}")
                elif attempt < retry_count - 1:
                    wait_time = backoff_factor * (2 ** attempt)
                    logger.warning(f"Request failed. Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    raise BadRequestException(f"API request failed: {str(e)}")
            except Exception as e:
                if attempt < retry_count - 1:
                    wait_time = backoff_factor * (2 ** attempt)
                    logger.warning(f"Request error. Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    raise BadRequestException(f"Request failed: {str(e)}")
        
        raise BadRequestException("Max retry attempts exceeded")
    
    def test_connection(self) -> bool:
        """Test if the connection to Confluence is working"""
        try:
            self._make_request('GET', '/wiki/rest/api/space?limit=1')
            return True
        except:
            return False
    
    def get_spaces(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all available spaces"""
        spaces = []
        start = 0
        
        while True:
            response = self._make_request(
                'GET',
                '/wiki/rest/api/space',
                params={'start': start, 'limit': limit, 'expand': 'description.plain,homepage'}
            )
            
            spaces.extend(response.get('results', []))
            
            if 'next' not in response.get('_links', {}):
                break
            
            start += limit
            
        return spaces
    
    def get_space_content(
        self, 
        space_key: str, 
        content_type: str = "page",
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get all content in a space"""
        contents = []
        start = 0
        
        while True:
            response = self._make_request(
                'GET',
                f'/wiki/rest/api/content',
                params={
                    'spaceKey': space_key,
                    'type': content_type,
                    'start': start,
                    'limit': limit,
                    'expand': 'body.storage,version,history,ancestors,children.page'
                }
            )
            
            contents.extend(response.get('results', []))
            
            if 'next' not in response.get('_links', {}):
                break
                
            start += limit
            
        return contents
    
    def get_page_by_id(
        self, 
        page_id: str,
        expand: str = "body.storage,version,history,ancestors,children.page,children.attachment"
    ) -> Dict[str, Any]:
        """Get a specific page by ID"""
        return self._make_request(
            'GET',
            f'/wiki/rest/api/content/{page_id}',
            params={'expand': expand}
        )
    
    def get_page_tree(self, page_id: str) -> List[Dict[str, Any]]:
        """Get a page and all its descendants"""
        pages = []
        to_process = [page_id]
        processed = set()
        
        while to_process:
            current_id = to_process.pop(0)
            if current_id in processed:
                continue
                
            try:
                page = self.get_page_by_id(current_id)
                pages.append(page)
                processed.add(current_id)
                
                # Add children to process queue
                children = page.get('children', {}).get('page', {}).get('results', [])
                for child in children:
                    if child['id'] not in processed:
                        to_process.append(child['id'])
                        
            except NotFoundException:
                logger.warning(f"Page {current_id} not found, skipping")
                
        return pages
    
    def get_attachments(self, page_id: str) -> List[Dict[str, Any]]:
        """Get attachments for a page"""
        attachments = []
        start = 0
        limit = 100
        
        while True:
            response = self._make_request(
                'GET',
                f'/wiki/rest/api/content/{page_id}/child/attachment',
                params={'start': start, 'limit': limit, 'expand': 'version'}
            )
            
            attachments.extend(response.get('results', []))
            
            if 'next' not in response.get('_links', {}):
                break
                
            start += limit
            
        return attachments
    
    def download_attachment(self, download_url: str) -> bytes:
        """Download an attachment"""
        full_url = urljoin(self.base_url, download_url)
        response = self.session.get(full_url)
        response.raise_for_status()
        return response.content
    
    def search_content(
        self,
        cql: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Search content using CQL (Confluence Query Language)"""
        results = []
        start = 0
        
        while True:
            response = self._make_request(
                'GET',
                '/wiki/rest/api/content/search',
                params={
                    'cql': cql,
                    'start': start,
                    'limit': limit,
                    'expand': 'body.storage,version,space'
                }
            )
            
            results.extend(response.get('results', []))
            
            if 'next' not in response.get('_links', {}):
                break
                
            start += limit
            
        return results
    
    def get_page_history(self, page_id: str) -> Dict[str, Any]:
        """Get version history of a page"""
        return self._make_request(
            'GET',
            f'/wiki/rest/api/content/{page_id}/version',
            params={'expand': 'content'}
        )
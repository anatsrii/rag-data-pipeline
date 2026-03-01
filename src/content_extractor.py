"""
Content Extractor Module
========================

Extracts and processes content from HTML pages, converting to Markdown.
"""

import re
import html2text
from pathlib import Path
from typing import Optional, Dict, List, Any, Tuple
from urllib.parse import urljoin, urlparse
from datetime import datetime
import logging

from bs4 import BeautifulSoup, NavigableString

from src.config_loader import ConfigLoader


logger = logging.getLogger(__name__)


class ContentExtractor:
    """Extract and convert HTML content to Markdown."""
    
    def __init__(self, config: Optional[ConfigLoader] = None):
        """
        Initialize content extractor.
        
        Args:
            config: Configuration loader instance
        """
        self.config = config or ConfigLoader()
        
        # Initialize html2text converter
        self.h2t = html2text.HTML2Text()
        self._configure_html2text()
    
    def _configure_html2text(self) -> None:
        """Configure html2text settings."""
        # Body width: 0 means no wrapping
        self.h2t.body_width = 0
        
        # Keep links
        self.h2t.ignore_links = False
        
        # Keep images
        self.h2t.ignore_images = not self.config.get('processing.extract_images', False)
        
        # Keep tables
        self.h2t.ignore_tables = False
        
        # Use proper emphasis
        self.h2t.emphasis_mark = '*'
        
        # Strong emphasis
        self.h2t.strong_mark = '**'
        
        # Protect links
        self.h2t.protect_links = True
        
        # Wrap list items
        self.h2t.wrap_list_items = False
        
        # Skip internal links
        self.h2t.skip_internal_links = False
    
    def extract_content(self, html: str, url: str) -> Optional[Dict[str, Any]]:
        """
        Extract main content from HTML.
        
        Args:
            html: Raw HTML content
            url: Source URL
            
        Returns:
            Dictionary with extracted content or None if extraction failed
        """
        try:
            # Clean encoding issues (remove \xa0 and other special chars)
            html = html.replace('\xa0', ' ').replace('\u00b6', '')
            
            soup = BeautifulSoup(html, 'lxml')
            
            # Remove unwanted elements
            self._remove_noise(soup)
            
            # Find main content
            main_content = self._find_main_content(soup)
            
            if not main_content:
                logger.warning(f"No main content found for {url}")
                return None
            
            # Extract metadata
            metadata = self._extract_metadata(soup, url, main_content)
            
            # Extract headings structure
            headings = self._extract_headings(main_content)
            
            # Convert to markdown
            markdown = self._convert_to_markdown(main_content, url)
            
            # Clean up markdown
            markdown = self._clean_markdown(markdown)
            
            # Check minimum content length
            min_length = self.config.get('processing.min_content_length', 100)
            if len(markdown) < min_length:
                logger.warning(f"Content too short ({len(markdown)} chars) for {url}")
                return None
            
            return {
                'title': metadata.get('title', 'Untitled'),
                'markdown': markdown,
                'headings': headings,
                'metadata': metadata,
                'word_count': len(markdown.split()),
                'char_count': len(markdown)
            }
            
        except Exception as e:
            logger.error(f"Error extracting content from {url}: {e}")
            return None
    
    def _remove_noise(self, soup: BeautifulSoup) -> None:
        """
        Remove unwanted elements from soup.
        
        Args:
            soup: BeautifulSoup object
        """
        remove_selectors = self.config.get_remove_selectors()
        
        for selector in remove_selectors:
            try:
                for element in soup.select(selector):
                    element.decompose()
            except Exception:
                pass
    
    def _find_main_content(self, soup: BeautifulSoup) -> Optional[BeautifulSoup]:
        """
        Find main content area in the page.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            Main content element or None
        """
        selectors = self.config.get_selectors()
        main_selector = selectors.get('main_content', 'main, article, .document')
        
        # Try each selector
        for selector in main_selector.split(','):
            selector = selector.strip()
            content = soup.select_one(selector)
            if content:
                return content
        
        # Fallback: find element with most text
        return self._find_largest_content(soup)
    
    def _find_largest_content(self, soup: BeautifulSoup) -> Optional[BeautifulSoup]:
        """
        Find the element with the most text content.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            Element with most content
        """
        candidates = ['article', 'main', 'div[role="main"]', '.content', '#content', 'body']
        
        best_elem = None
        best_length = 0
        
        for candidate in candidates:
            elem = soup.select_one(candidate)
            if elem:
                text_length = len(elem.get_text(strip=True))
                if text_length > best_length:
                    best_length = text_length
                    best_elem = elem
        
        return best_elem
    
    def _clean_text(self, text: str) -> str:
        """Clean text by removing special characters and fixing encoding issues."""
        if not text:
            return ''
        
        # Fix common UTF-8 encoding artifacts (Windows-1252 misinterpretation)
        # These are common when UTF-8 content is read as Latin-1/Windows-1252
        replacements = {
            '\xa0': ' ',      # Non-breaking space
            '\u00b6': '',     # Pilcrow/paragraph symbol
            '\xc2': '',       # C2 prefix byte
            '¶': '',          # Paragraph symbol
            'Â': '',          # C2 interpreted as Windows-1252
            'â\x80\xa6': '...',  # Ellipsis (UTF-8: E2 80 A6)
            'â\x80\x93': '-',    # En dash (UTF-8: E2 80 93)
            'â\x80\x99': "'",    # Right single quote (UTF-8: E2 80 99)
            'â\x80\x98': "'",    # Left single quote (UTF-8: E2 80 98)
            'â\x80\x9c': '"',    # Left double quote (UTF-8: E2 80 9C)
            'â\x80\x9d': '"',    # Right double quote (UTF-8: E2 80 9D)
            'â': '',          # Generic 'a' with circumflex (catch remaining)
            '\x80': '',       # Control character
            '\x99': "'",      # Common single quote misencoding
            '\x9c': '"',      # Common double quote misencoding
            '\x9d': '"',      # Common double quote misencoding
            '\x98': "'",      # Common single quote misencoding
            '\x94': '"',      # Common double quote misencoding
            "\"'": "'",       # Fix double+single quote
            "'\"": "'",       # Fix single+double quote
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        # Clean up multiple spaces
        text = ' '.join(text.split())
        return text.strip()

    def _extract_metadata(self, soup: BeautifulSoup, url: str, 
                         content: BeautifulSoup) -> Dict[str, Any]:
        """
        Extract metadata from the page.
        
        Args:
            soup: BeautifulSoup object
            url: Source URL
            content: Main content element
            
        Returns:
            Dictionary with metadata
        """
        metadata = {
            'source_url': url,
            'version': '19.0',
            'last_crawled': datetime.now().isoformat(),
        }
        
        # Extract title
        title_selectors = self.config.get_selectors().get('title', 'h1, .document-title')
        for selector in title_selectors.split(','):
            title_elem = soup.select_one(selector.strip())
            if title_elem:
                metadata['title'] = self._clean_text(title_elem.get_text(strip=True))
                break
        
        # Fallback to page title
        if 'title' not in metadata:
            title_tag = soup.find('title')
            if title_tag:
                metadata['title'] = self._clean_text(title_tag.get_text(strip=True))
            else:
                metadata['title'] = 'Untitled'
        
        # Extract category from URL
        metadata['category'] = self._categorize_url(url)
        
        # Extract description
        desc_meta = soup.find('meta', attrs={'name': 'description'})
        if desc_meta:
            metadata['description'] = desc_meta.get('content', '')
        
        # Extract keywords
        keywords_meta = soup.find('meta', attrs={'name': 'keywords'})
        if keywords_meta:
            metadata['keywords'] = keywords_meta.get('content', '')
        
        return metadata
    
    def _extract_headings(self, content: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        Extract heading structure from content.
        
        Args:
            content: Main content element
            
        Returns:
            List of headings with level and text
        """
        headings = []
        heading_selectors = self.config.get_selectors().get('headings', 'h1, h2, h3, h4, h5, h6')
        
        for heading in content.select(heading_selectors):
            level = int(heading.name[1])  # h1 -> 1, h2 -> 2, etc.
            text = self._clean_text(heading.get_text(strip=True))
            
            # Extract anchor ID if present
            anchor_id = heading.get('id', '')
            if not anchor_id and heading.find('a', id=True):
                anchor_id = heading.find('a', id=True).get('id', '')
            
            headings.append({
                'level': level,
                'text': text,
                'anchor': anchor_id
            })
        
        return headings
    
    def _convert_to_markdown(self, content: BeautifulSoup, base_url: str) -> str:
        """
        Convert HTML content to Markdown.
        
        Args:
            content: HTML content element
            base_url: Base URL for resolving relative links
            
        Returns:
            Markdown string
        """
        # Process code blocks before conversion
        self._process_code_blocks(content)
        
        # Process links
        self._process_links(content, base_url)
        
        # Convert to markdown
        markdown = self.h2t.handle(str(content))
        
        return markdown
    
    def _process_code_blocks(self, content: BeautifulSoup) -> None:
        """
        Process code blocks to preserve formatting.
        
        Args:
            content: BeautifulSoup content element
        """
        code_selectors = self.config.get_selectors().get('code_blocks', 'pre, code')
        
        for pre in content.find_all('pre'):
            # Try to detect language
            code_elem = pre.find('code')
            language = ''
            
            if code_elem:
                # Check for language class
                classes = code_elem.get('class', [])
                for cls in classes:
                    if cls.startswith('language-') or cls.startswith('lang-'):
                        language = cls.split('-', 1)[1]
                        break
                    # Handle highlight.js style
                    if cls in ['python', 'javascript', 'js', 'html', 'xml', 'css', 
                              'bash', 'shell', 'json', 'yaml', 'sql', 'java', 'cpp']:
                        language = cls
                        break
            
            # Add language marker if found
            if language:
                pre['data-language'] = language
    
    def _process_links(self, content: BeautifulSoup, base_url: str) -> None:
        """
        Process links to make them absolute.
        
        Args:
            content: BeautifulSoup content element
            base_url: Base URL for resolving relative links
        """
        for link in content.find_all('a', href=True):
            href = link['href']
            
            # Skip anchors
            if href.startswith('#'):
                continue
            
            # Make absolute
            if not href.startswith(('http://', 'https://', 'mailto:')):
                link['href'] = urljoin(base_url, href)
    
    def _clean_markdown(self, markdown: str) -> str:
        """
        Clean up markdown text.
        
        Args:
            markdown: Raw markdown text
            
        Returns:
            Cleaned markdown
        """
        if self.config.get('processing.clean_whitespace', True):
            # Remove excessive blank lines
            markdown = re.sub(r'\n{4,}', '\n\n\n', markdown)
            
            # Remove trailing whitespace
            markdown = '\n'.join(line.rstrip() for line in markdown.split('\n'))
            
            # Clean up code blocks
            markdown = self._clean_code_blocks(markdown)
        
        # Clean text encoding issues in the entire markdown
        markdown = self._clean_text(markdown)
        
        # Remove permalink symbols and links (¶ character variations)
        # Remove patterns like [¶](<#anchor> "Permalink to this headline")
        markdown = re.sub(r'\[[\s]*\]\(<[^>]+>\s*"Permalink to this headline"\)', '', markdown)
        
        # Fix newlines - restore proper line breaks for headings
        markdown = re.sub(r'\n?\s*#{1,6}\s+', lambda m: '\n\n' + m.group().strip() + ' ', markdown)
        markdown = re.sub(r'\n\n\n+', '\n\n', markdown)
        
        return markdown.strip()
    
    def _clean_code_blocks(self, markdown: str) -> str:
        """
        Clean up code block formatting.
        
        Args:
            markdown: Markdown text
            
        Returns:
            Cleaned markdown with proper code blocks
        """
        # Fix code blocks that might have been broken
        lines = markdown.split('\n')
        result = []
        in_code_block = False
        
        for line in lines:
            # Detect code block start/end
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
            
            # Preserve indentation in code blocks
            if in_code_block:
                result.append(line)
            else:
                result.append(line)
        
        return '\n'.join(result)
    
    def _categorize_url(self, url: str) -> str:
        """
        Categorize URL based on path.
        
        Args:
            url: URL to categorize
            
        Returns:
            Category name
        """
        path = urlparse(url).path.lower()
        
        if '/developer' in path or '/reference' in path or '/api' in path:
            return 'developer'
        elif '/applications' in path or '/user' in path:
            return 'functional'
        elif '/administration' in path or '/installation' in path:
            return 'setup'
        else:
            return 'general'
    
    def save_markdown(self, content: Dict[str, Any], filepath: Path) -> bool:
        """
        Save markdown content to file.
        
        Args:
            content: Content dictionary from extract_content
            filepath: Path to save file
            
        Returns:
            True if saved successfully
        """
        try:
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            # Build frontmatter
            frontmatter = self._build_frontmatter(content['metadata'], content['headings'])
            
            # Combine frontmatter and content
            full_content = frontmatter + '\n\n' + content['markdown']
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(full_content)
            
            logger.info(f"Saved: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving markdown to {filepath}: {e}")
            return False
    
    def _build_frontmatter(self, metadata: Dict[str, Any], 
                          headings: List[Dict]) -> str:
        """
        Build YAML frontmatter for markdown file.
        
        Args:
            metadata: Metadata dictionary
            headings: List of headings
            
        Returns:
            YAML frontmatter string
        """
        lines = ['---']
        
        # Add metadata fields
        for key, value in metadata.items():
            if isinstance(value, str):
                # Escape special characters
                if ':' in value or '"' in value or '\n' in value:
                    value = f'"{value.replace("\"", "\\\"")}"'
                lines.append(f'{key}: {value}')
            else:
                lines.append(f'{key}: {value}')
        
        # Add headings structure
        if headings:
            lines.append('headings_structure:')
            for h in headings:
                indent = '  ' * (h['level'] - 1)
                lines.append(f'  {indent}- {h["text"]}')
        
        lines.append('---')
        
        return '\n'.join(lines)

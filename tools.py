"""
Tools Module
Provides web search and URL scraping capabilities for the research agents.
Enhanced with caching, retry logic, and better error handling.
"""

import requests
from bs4 import BeautifulSoup
from tavily import TavilyClient
from langchain.tools import tool
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from rich import print

from config import (
    TAVILY_API_KEY, MAX_SEARCH_RESULTS, MAX_SCRAPE_LENGTH, 
    REQUEST_TIMEOUT, MAX_RETRIES, RETRY_MIN_WAIT, RETRY_MAX_WAIT
)
from utils import get_cache_key, get_from_cache, save_to_cache, logger

# Initialize Tavily client
tavily = TavilyClient(api_key=TAVILY_API_KEY)

@tool
@retry(
    stop=stop_after_attempt(MAX_RETRIES),
    wait=wait_exponential(multiplier=1, min=RETRY_MIN_WAIT, max=RETRY_MAX_WAIT),
    retry=retry_if_exception_type((requests.exceptions.RequestException, Exception))
)
def web_search(query: str) -> str:
    """
    Search the web for recent and reliable information on a topic.
    Enhanced with caching and retry logic.
    
    Args:
        query: The search query string
        
    Returns:
        Formatted string with titles, URLs, and content snippets
    """
    logger.info(f"Web search query: {query}")
    
    # Check cache first
    cache_key = get_cache_key(f"search_{query}")
    cached_result = get_from_cache(cache_key)
    
    if cached_result:
        logger.info("Returning cached search results")
        return cached_result
    
    try:
        results = tavily.search(query=query, max_results=MAX_SEARCH_RESULTS)
        
        if not results.get('results'):
            logger.warning("No search results found")
            return "No search results found."
        
        formatted_results = []
        for idx, result in enumerate(results['results'], 1):
            formatted_results.append(
                f"[{idx}] Title: {result.get('title', 'N/A')}\n"
                f"    URL: {result.get('url', 'N/A')}\n"
                f"    Snippet: {result.get('content', '')[:300]}...\n"
            )
        
        output = "\n" + "="*60 + "\n".join(formatted_results)
        
        # Cache the results
        save_to_cache(cache_key, output)
        
        logger.info(f"Found {len(results['results'])} search results")
        return output
    
    except Exception as e:
        logger.error(f"Error during web search: {str(e)}")
        return f"Error during web search: {str(e)}"

@tool
@retry(
    stop=stop_after_attempt(MAX_RETRIES),
    wait=wait_exponential(multiplier=1, min=RETRY_MIN_WAIT, max=RETRY_MAX_WAIT),
    retry=retry_if_exception_type((requests.exceptions.RequestException,))
)
def scrape_url(url: str) -> str:
    """
    Scrape and return clean text content from a given URL.
    Enhanced with caching, retry logic, and better error handling.
    
    Args:
        url: The URL to scrape
        
    Returns:
        Cleaned text content from the webpage
    """
    logger.info(f"Scraping URL: {url}")
    
    # Check cache first
    cache_key = get_cache_key(f"scrape_{url}")
    cached_result = get_from_cache(cache_key)
    
    if cached_result:
        logger.info("Returning cached scraped content")
        return cached_result
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                         "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        response = requests.get(url, timeout=REQUEST_TIMEOUT, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Remove unwanted tags
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "iframe"]):
            tag.decompose()
        
        # Extract text
        text = soup.get_text(separator=" ", strip=True)
        
        # Limit length
        if len(text) > MAX_SCRAPE_LENGTH:
            text = text[:MAX_SCRAPE_LENGTH] + "... [Content truncated]"
        
        result = text if text else "No readable content found on the page."
        
        # Cache the results
        save_to_cache(cache_key, result)
        
        logger.info(f"Successfully scraped {len(text)} characters from {url}")
        return result
    
    except requests.exceptions.Timeout:
        error_msg = f"Error: Request timeout while accessing {url}"
        logger.error(error_msg)
        return error_msg
    except requests.exceptions.RequestException as e:
        error_msg = f"Error scraping URL: {str(e)}"
        logger.error(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(error_msg)
        return error_msg


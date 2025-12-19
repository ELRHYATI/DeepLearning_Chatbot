"""
Web Search Service
Provides web search functionality to enrich QA responses with real-time information
"""
import os
import httpx
from typing import Dict, List, Optional
from app.utils.logger import get_logger
import json
import time

logger = get_logger()


class WebSearchService:
    """Service for web search to enhance QA with real-time information"""
    
    def __init__(self):
        self.use_web_search = os.getenv("ENABLE_WEB_SEARCH", "true").lower() == "true"
        self.search_provider = os.getenv("WEB_SEARCH_PROVIDER", "duckduckgo")  # duckduckgo, tavily, serpapi
        self.tavily_api_key = os.getenv("TAVILY_API_KEY", "")
        self.serpapi_key = os.getenv("SERPAPI_KEY", "")
        self.max_results = int(os.getenv("WEB_SEARCH_MAX_RESULTS", "5"))
        self.timeout = 10.0
        
    def search(self, query: str, max_results: Optional[int] = None) -> List[Dict]:
        """
        Search the web for information
        
        Args:
            query: Search query
            max_results: Maximum number of results (defaults to self.max_results)
            
        Returns:
            List of search results with title, url, snippet
        """
        if not self.use_web_search:
            logger.debug("Web search is disabled")
            return []
        
        max_results = max_results or self.max_results
        
        try:
            if self.search_provider == "tavily" and self.tavily_api_key:
                return self._search_tavily(query, max_results)
            elif self.search_provider == "serpapi" and self.serpapi_key:
                return self._search_serpapi(query, max_results)
            else:
                # Default to DuckDuckGo (free, no API key needed)
                return self._search_duckduckgo(query, max_results)
        except Exception as e:
            logger.error(f"Web search failed: {e}", exc_info=e)
            return []
    
    def _search_duckduckgo(self, query: str, max_results: int) -> List[Dict]:
        """
        Search using DuckDuckGo (free, no API key required)
        Uses DuckDuckGo's instant answer API and web search
        """
        try:
            results = []
            
            # Try instant answer API first (faster, but limited)
            try:
                instant_url = "https://api.duckduckgo.com/"
                params = {
                    "q": query,
                    "format": "json",
                    "no_html": "1",
                    "skip_disambig": "1"
                }
                
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.get(instant_url, params=params)
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Extract instant answer
                        if data.get("AbstractText"):
                            results.append({
                                "title": data.get("Heading", query),
                                "url": data.get("AbstractURL", ""),
                                "snippet": data.get("AbstractText", ""),
                                "source": "DuckDuckGo Instant Answer"
                            })
                        
                        # Extract related topics
                        for topic in data.get("RelatedTopics", [])[:max_results-1]:
                            if isinstance(topic, dict) and topic.get("Text"):
                                results.append({
                                    "title": topic.get("Text", "").split(" - ")[0] if " - " in topic.get("Text", "") else query,
                                    "url": topic.get("FirstURL", ""),
                                    "snippet": topic.get("Text", ""),
                                    "source": "DuckDuckGo"
                                })
                                if len(results) >= max_results:
                                    break
            except Exception as e:
                logger.debug(f"DuckDuckGo instant answer failed: {e}")
            
            # If we don't have enough results, use HTML scraping (simplified)
            if len(results) < max_results:
                try:
                    # Use DuckDuckGo HTML search as fallback
                    search_url = "https://html.duckduckgo.com/html/"
                    params = {"q": query}
                    
                    with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
                        response = client.get(search_url, params=params)
                        if response.status_code == 200:
                            # Simple HTML parsing (basic implementation)
                            html = response.text
                            
                            # Try to extract results (basic regex-based extraction)
                            import re
                            # Look for result links
                            link_pattern = r'<a class="result__a"[^>]*href="([^"]*)"[^>]*>([^<]*)</a>'
                            snippet_pattern = r'<a class="result__snippet"[^>]*>([^<]*)</a>'
                            
                            links = re.findall(link_pattern, html)
                            snippets = re.findall(snippet_pattern, html)
                            
                            for i, (url, title) in enumerate(links[:max_results - len(results)]):
                                snippet = snippets[i] if i < len(snippets) else ""
                                results.append({
                                    "title": title.strip(),
                                    "url": url,
                                    "snippet": snippet.strip(),
                                    "source": "DuckDuckGo Web"
                                })
                                if len(results) >= max_results:
                                    break
                except Exception as e:
                    logger.debug(f"DuckDuckGo HTML search failed: {e}")
            
            return results[:max_results]
            
        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
            return []
    
    def _search_tavily(self, query: str, max_results: int) -> List[Dict]:
        """
        Search using Tavily API (requires API key)
        More reliable and structured results
        """
        try:
            url = "https://api.tavily.com/search"
            headers = {"Content-Type": "application/json"}
            data = {
                "api_key": self.tavily_api_key,
                "query": query,
                "max_results": max_results,
                "search_depth": "basic"
            }
            
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, json=data, headers=headers)
                if response.status_code == 200:
                    result_data = response.json()
                    results = []
                    
                    for item in result_data.get("results", []):
                        results.append({
                            "title": item.get("title", ""),
                            "url": item.get("url", ""),
                            "snippet": item.get("content", ""),
                            "source": "Tavily"
                        })
                    
                    return results[:max_results]
                else:
                    logger.warning(f"Tavily API error: {response.status_code}")
                    return []
        except Exception as e:
            logger.error(f"Tavily search error: {e}")
            return []
    
    def _search_serpapi(self, query: str, max_results: int) -> List[Dict]:
        """
        Search using SerpAPI (requires API key)
        Provides Google search results
        """
        try:
            url = "https://serpapi.com/search"
            params = {
                "api_key": self.serpapi_key,
                "q": query,
                "engine": "google",
                "num": max_results,
                "hl": "fr",  # French language
                "gl": "fr"   # France country
            }
            
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    results = []
                    
                    # Extract organic results
                    for item in data.get("organic_results", [])[:max_results]:
                        results.append({
                            "title": item.get("title", ""),
                            "url": item.get("link", ""),
                            "snippet": item.get("snippet", ""),
                            "source": "SerpAPI (Google)"
                        })
                    
                    return results
                else:
                    logger.warning(f"SerpAPI error: {response.status_code}")
                    return []
        except Exception as e:
            logger.error(f"SerpAPI search error: {e}")
            return []
    
    def get_context_from_search(self, query: str, max_results: int = 3) -> str:
        """
        Get formatted context string from web search results
        
        Args:
            query: Search query
            max_results: Number of results to include
            
        Returns:
            Formatted context string
        """
        results = self.search(query, max_results)
        
        if not results:
            return ""
        
        context_parts = []
        for i, result in enumerate(results, 1):
            snippet = result.get("snippet", "").strip()
            if snippet:
                context_parts.append(f"[Source {i}: {result.get('title', 'Unknown')}] {snippet}")
        
        return "\n\n".join(context_parts)
    
    def should_use_web_search(self, question: str) -> bool:
        """
        Determine if web search should be used for a question
        
        Args:
            question: The question to analyze
            
        Returns:
            True if web search should be used
        """
        if not self.use_web_search:
            return False
        
        question_lower = question.lower()
        
        # Keywords that suggest need for current/recent information
        time_sensitive_keywords = [
            "récent", "actuel", "aujourd'hui", "maintenant", "2024", "2025",
            "dernière", "nouveau", "actualité", "news", "événement"
        ]
        
        # Keywords that suggest need for specific facts or data
        fact_keywords = [
            "combien", "quel est", "quelle est", "qui est", "où est",
            "quand", "comment", "pourquoi", "statistique", "donnée"
        ]
        
        # Check if question needs web search
        has_time_sensitive = any(keyword in question_lower for keyword in time_sensitive_keywords)
        has_fact_query = any(keyword in question_lower for keyword in fact_keywords)
        
        # Use web search for time-sensitive or fact-based queries
        return has_time_sensitive or has_fact_query


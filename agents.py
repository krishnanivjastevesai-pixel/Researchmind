"""
AI Agents Module
Defines search agent, reader agent, writer chain, and critic chain
using Groq Cloud LLM for fast inference.
Simplified to work directly with tools without complex agent frameworks.
"""

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from config import GROQ_API_KEY, GROQ_MODEL, MODEL_TEMPERATURE
from tools import web_search, scrape_url
from utils import logger

# Initialize Groq LLM
try:
    llm = ChatGroq(
        model=GROQ_MODEL,
        temperature=MODEL_TEMPERATURE,
        api_key=GROQ_API_KEY
    )
    logger.info(f"Initialized Groq LLM with model: {GROQ_MODEL}")
except Exception as e:
    logger.error(f"Failed to initialize Groq LLM: {e}")
    raise


# ============================================
# Agent 1: Search Agent (Simplified)
# ============================================
def build_search_agent():
    """
    Creates a simple search function that uses web_search tool.
    Returns a callable that mimics agent behavior.
    """
    def search_executor(input_dict):
        query = input_dict.get("input", "")
        logger.info(f"Search agent executing query: {query}")
        result = web_search.invoke(query)
        return {"output": result}
    
    return type('SearchAgent', (), {'invoke': lambda self, x: search_executor(x)})()


# ============================================
# Agent 2: Reader Agent (Simplified)
# ============================================
def build_reader_agent():
    """
    Creates a simple reader function that uses scrape_url tool.
    Returns a callable that mimics agent behavior.
    """
    def reader_executor(input_dict):
        text = input_dict.get("input", "")
        logger.info(f"Reader agent processing: {text[:100]}...")
        
        # Extract URL from the input text
        import re
        urls = re.findall(r'https?://[^\s]+', text)
        
        if urls:
            url = urls[0]  # Use first URL found
            logger.info(f"Scraping URL: {url}")
            result = scrape_url.invoke(url)
        else:
            result = "No URL found in the input to scrape."
        
        return {"output": result}
    
    return type('ReaderAgent', (), {'invoke': lambda self, x: reader_executor(x)})()



# ============================================
# Chain 1: Writer Chain
# ============================================
writer_prompt = ChatPromptTemplate.from_messages([
    ("system", 
     "You are an expert research writer with a PhD-level understanding of complex topics. "
     "Write clear, well-structured, and insightful reports that are both comprehensive and accessible. "
     "Use proper markdown formatting for better readability."),
    ("human", 
     """Write a detailed research report on the topic below.

**Topic:** {topic}

**Research Gathered:**
{research}

**Required Structure:**
1. **Introduction** - Provide context and overview
2. **Key Findings** - Present at least 3-5 well-explained points with supporting evidence
3. **Analysis** - Discuss implications and significance
4. **Conclusion** - Summarize insights and future outlook
5. **Sources** - List all URLs and references used

**Guidelines:**
- Be detailed, factual, and professional
- Use markdown formatting (headers, lists, bold, italic)
- Include specific data, statistics, or quotes when available
- Maintain an objective, analytical tone
- Aim for 800-1200 words"""),
])

writer_chain = writer_prompt | llm | StrOutputParser()

# ============================================
# Chain 2: Critic Chain
# ============================================
critic_prompt = ChatPromptTemplate.from_messages([
    ("system", 
     "You are a sharp, constructive research critic with expertise in academic writing and journalism. "
     "Evaluate reports based on accuracy, depth, clarity, structure, and evidence quality. "
     "Be honest, specific, and actionable in your feedback."),
    ("human", 
     """Review the research report below and evaluate it comprehensively.

**Report:**
{report}

**Respond in this exact format:**

**Score:** X/10

**Strengths:**
- [List 2-3 specific strengths]

**Areas to Improve:**
- [List 2-3 specific areas needing improvement]

**Evidence Quality:** [Rate the use of sources and data]

**Clarity & Structure:** [Assess readability and organization]

**One-Line Verdict:**
[Provide a concise overall assessment]"""),
])

critic_chain = critic_prompt | llm | StrOutputParser()


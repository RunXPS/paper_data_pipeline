import os
import tempfile
import urllib.request
import fitz  # PyMuPDF
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

# 1. Define the exact JSON schema we want Gemini to output using Pydantic
class QuantStrategyAnalysis(BaseModel):
    core_alpha: str = Field(description="The actual trading rule, mathematical signal, or predictive model proposed.")
    asset_class: str = Field(description="The target asset class (e.g., Equities, FX, Options, Crypto, Multi-Asset).")
    claimed_performance: str = Field(description="Specific metrics claimed (e.g., Sharpe ratio, win rate, drawdown) or 'Not explicitly stated'.")
    implementation_difficulty: str = Field(description="Assessment of implementation difficulty (e.g., Low, Medium, High) with a 1-sentence justification.")
    executive_summary: str = Field(description="A concise, 2-sentence summary of the strategy and its edge.")

def download_and_extract_pdf(arxiv_url):
    """
    Converts an arXiv abstract URL to a PDF URL, downloads it to a 
    temporary file, and extracts all text using PyMuPDF.
    """
    # Convert https://arxiv.org/abs/1234.5678 to https://arxiv.org/pdf/1234.5678.pdf
    pdf_url = arxiv_url.replace("/abs/", "/pdf/") + ".pdf"
    print(f"Downloading PDF from {pdf_url}...")
    
    try:
        # Create a temporary file that deletes itself when we are done
        with tempfile.NamedTemporaryFile(delete=True, suffix=".pdf") as temp_pdf:
            # Set a standard User-Agent so arXiv doesn't block the automated request
            req = urllib.request.Request(pdf_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                temp_pdf.write(response.read())
            
            # Extract text using PyMuPDF
            doc = fitz.open(temp_pdf.name)
            full_text = ""
            for page in doc:
                full_text += page.get_text()
                
            print(f"Extraction complete. Read {len(full_text)} characters.")
            return full_text
            
    except Exception as e:
        print(f"Failed to download or parse PDF: {e}")
        return None

def evaluate_strategy_with_gemini(paper_text, api_key):
    """
    Sends the full paper text to Gemini 2.5 Flash and forces the response
    to match our QuantStrategyAnalysis Pydantic schema.
    """
    if not paper_text:
        return None
        
    print("Sending full text to Gemini for deep evaluation...")
    
    # Initialize the official Google GenAI client
    client = genai.Client(api_key=api_key)
    
    # We use Gemini 2.5 Flash: It has a 1M token context window, making it 
    # perfect for swallowing entire research papers in seconds.
    model_id = "gemini-2.5-flash"
    
    prompt = (
        "You are a Senior Quantitative Researcher at a top proprietary trading firm. "
        "Read the following academic paper and extract the specifics of the trading strategy proposed. "
        "Filter out the academic noise and focus entirely on how to implement the alpha.\n\n"
        f"PAPER TEXT:\n{paper_text}"
    )
    
    try:
        # We pass our Pydantic model to the response_schema config.
        # This guarantees Gemini returns a perfectly formatted JSON object matching our fields.
        response = client.models.generate_content(
            model=model_id,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=QuantStrategyAnalysis,
                temperature=0.1 # Keep it highly deterministic and factual
            )
        )
        
        # The SDK automatically parses the JSON into our Pydantic object
        return response.parsed
        
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return None
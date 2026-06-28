import os
import sys
import time
from dotenv import load_dotenv

from api_retrieval import fetch_recent_quant_papers
from llm_screener import filter_promising_papers
from pdf_analyzer import download_and_extract_pdf, evaluate_strategy_with_gemini

load_dotenv()

def main():
    print("=== Initiating Deep-Search Quant Pipeline ===\n")
    
    # 1. Credential Management
    groq_api_key = os.environ.get("GROQ_API_KEY")
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    
    if not groq_api_key or not gemini_api_key:
        print("CRITICAL ERROR: API keys missing.")
        print("Please set both GROQ_API_KEY and GEMINI_API_KEY environment variables.")
        sys.exit(1)

    # Search Configuration
    batch_size = 10
    max_batches = 5
    current_start_index = 0
    actionable_papers = []

    # Phase 1 & 2: Search and Screen
    for batch_num in range(1, max_batches + 1):
        print(f"\n--- Searching Batch {batch_num}/{max_batches} (Index {current_start_index}) ---")
        
        raw_papers = fetch_recent_quant_papers(start=current_start_index, max_results=batch_size)
        if not raw_papers:
            break

        found_papers = filter_promising_papers(raw_papers, groq_api_key)
        
        if found_papers:
            actionable_papers.extend(found_papers)
            print(f"SUCCESS: Found {len(found_papers)} actionable strategy(s)!")
            break  # Stop searching once we find a good batch
        else:
            print("Batch was entirely noise. Moving deeper...")
            current_start_index += batch_size
            time.sleep(3)

    if not actionable_papers:
        print("\n[HALT] No strategies found in recent archives. Exiting.")
        sys.exit(0)

    # Phase 3: Deep Evaluation with Gemini
    print("\n=== Phase 3: Deep Paper Evaluation ===")
    
    final_reports = []
    
    for i, paper in enumerate(actionable_papers, 1):
        print(f"\nAnalyzing Paper [{i}/{len(actionable_papers)}]: {paper['title']}")
        
        # Download and extract the full PDF text
        full_text = download_and_extract_pdf(paper['link'])
        
        if full_text:
            # Pass the text to Gemini
            analysis = evaluate_strategy_with_gemini(full_text, gemini_api_key)
            
            if analysis:
                # Store the results
                paper['deep_analysis'] = analysis
                final_reports.append(paper)
                
                # Print the structured findings
                print(f"\n--- GEMINI STRATEGY EXTRACTION ---")
                print(f"Asset Class: {analysis.asset_class}")
                print(f"Core Alpha:  {analysis.core_alpha}")
                print(f"Performance: {analysis.claimed_performance}")
                print(f"Difficulty:  {analysis.implementation_difficulty}")
                print(f"Summary:     {analysis.executive_summary}")
                print("-" * 40)
            else:
                print("Failed to evaluate paper with Gemini.")

    print("\n=== Pipeline Execution Complete ===")

if __name__ == "__main__":
    main()
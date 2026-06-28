import os
import sys
import time
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

from api_retrieval import fetch_recent_quant_papers
from llm_screener import filter_promising_papers
from pdf_analyzer import download_and_extract_pdf, evaluate_strategy_with_gemini
from email_sender import send_weekly_email

load_dotenv()

def main():
    print("=== Initiating Daily Quant Pipeline Cron Job ===\n")
    
    # 1. Credential Management
    groq_api_key = os.environ.get("GROQ_API_KEY")
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    
    if not groq_api_key or not gemini_api_key:
        print("CRITICAL ERROR: API keys missing.")
        print("Please set both GROQ_API_KEY and GEMINI_API_KEY environment variables.")
        sys.exit(1)

    # Search Configuration
    batch_size = 20  # Increased batch size for more efficient daily fetching
    current_start_index = 0
    actionable_papers = []
    keep_fetching = True
    
    # Target yesterday's date to capture a full 24-hour cycle
    target_date = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')
    print(f"Targeting papers published on: {target_date}")

    # Phase 1 & 2: Search and Screen
    while keep_fetching:
        print(f"\n--- Searching Batch (Index {current_start_index}) ---")
        
        # Pass target_date directly to the API fetcher
        raw_papers = fetch_recent_quant_papers(start=current_start_index, max_results=batch_size, target_date=target_date)
        
        if not raw_papers:
            print("No more papers returned from arXiv API for this date.")
            break

        # The API now filters by date natively, so everything returned belongs to target_date
        papers_to_screen = raw_papers

        if papers_to_screen:
            found_papers = filter_promising_papers(papers_to_screen, groq_api_key)
            if found_papers:
                actionable_papers.extend(found_papers)
                print(f"SUCCESS: Found {len(found_papers)} actionable strategy(s) in this batch!")

        # If the API returned fewer papers than our max request size, we have reached the end
        if len(raw_papers) < batch_size:
            keep_fetching = False
        else:
            print("Moving deeper into the archive to find the rest of yesterday's papers...")
            current_start_index += batch_size
            time.sleep(3)

    if not actionable_papers:
        print(f"\n[HALT] No strategies found for {target_date}.")
        final_reports = []
    else:
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
                    # Convert the Pydantic analysis model to a standard dictionary for JSON serialization
                    paper['deep_analysis'] = analysis.model_dump() if hasattr(analysis, 'model_dump') else analysis.dict()
                    final_reports.append(paper)
                    
                    # Print the structured findings
                    print(f"--- Extracted Core Alpha for {paper['title'][:30]}... ---")
                else:
                    print("Failed to evaluate paper with Gemini.")

    # Phase 4: Accumulation and Email Notification
    print("\n=== Phase 4: Data Accumulation & Delivery ===")
    
    # CRITICAL FOR CRON: Enforce absolute paths so the JSON file is always found
    script_dir = os.path.dirname(os.path.abspath(__file__))
    accumulation_file = os.path.join(script_dir, "accumulated_papers.json")
    accumulated_papers = []
    
    # 1. Load any papers accumulated earlier in the week
    if os.path.exists(accumulation_file):
        try:
            with open(accumulation_file, "r") as f:
                accumulated_papers = json.load(f)
        except json.JSONDecodeError:
            print("Warning: Existing JSON accumulation file could not be read. Starting fresh.")
            
    # 2. Add today's findings
    if final_reports:
        accumulated_papers.extend(final_reports)
        
        # Save the updated list back to the file
        with open(accumulation_file, "w") as f:
            json.dump(accumulated_papers, f, indent=4)
            
    print(f"Saved {len(final_reports)} new papers today. Total accumulated this week: {len(accumulated_papers)}")

    # 3. Check if today is the day to send the email (0 = Monday, 6 = Sunday)
    today_weekday = datetime.today().weekday()
    EMAIL_DAY = 6  # Sending on Sunday
    
    if today_weekday == EMAIL_DAY:
        print("Today is Sunday! Triggering weekly email summary...")
        if accumulated_papers:
            success = send_weekly_email(accumulated_papers)
            if success:
                # Clear the accumulation file for the new week
                os.remove(accumulation_file)
                print("Accumulation file cleared for the new week.")
        else:
            print("No papers were found this entire week. Skipping email.")
    else:
        days_until = EMAIL_DAY - today_weekday
        print(f"Today is not the scheduled email day. (Skipping transmission, {days_until} days until summary)")

    print("\n=== Pipeline Execution Complete ===")

if __name__ == "__main__":
    main()
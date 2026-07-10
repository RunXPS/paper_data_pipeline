import os
import sys
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

from api_retrieval import fetch_recent_quant_papers
from llm_screener import filter_promising_papers
from pdf_analyzer import download_and_extract_pdf, evaluate_strategy_with_gemini
from email_sender import send_weekly_email
from supabase_store import get_week_key, load_accumulated_papers, save_papers, clear_week

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

    week_key = get_week_key()
    accumulated_papers = load_accumulated_papers(week_key)

    if final_reports:
        save_papers(final_reports, week_key)
        accumulated_papers.extend(final_reports)

    print(f"Saved {len(final_reports)} new papers today. Total accumulated this week: {len(accumulated_papers)}")

    # Check if today is the day to send the email (0 = Monday, 6 = Sunday)
    today_weekday = datetime.today().weekday()
    EMAIL_DAY = 6  # Sending on Sunday

    if today_weekday == EMAIL_DAY:
        print("Today is Sunday! Triggering weekly email summary...")
        if accumulated_papers:
            success = send_weekly_email(
                accumulated_papers,
                os.environ.get("SENDER_EMAIL"),
                os.environ.get("SENDER_PASSWORD"),
                os.environ.get("RECEIVER_EMAIL"),
            )
            if success:
                clear_week(week_key)
        else:
            print("No papers were found this entire week. Skipping email.")
    else:
        days_until = EMAIL_DAY - today_weekday
        print(f"Today is not the scheduled email day. (Skipping transmission, {days_until} days until summary)")

    print("\n=== Pipeline Execution Complete ===")

if __name__ == "__main__":
    main()
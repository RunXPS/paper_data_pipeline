import json
import urllib.request
import urllib.parse
from groq import Groq

def screen_abstract_with_groq(title, abstract, api_key):
    """
    Evaluates a single paper abstract using Groq to determine if it contains
    a concrete, actionable trading strategy.
    """

    client = Groq(
        api_key=api_key,
    )

    # We use a strict system prompt to force a structured JSON output
    system_prompt = (
        "You are an expert quantitative research screener. Your job is to analyze academic abstracts "
        "and determine if the paper proposes a concrete, actionable systematic trading strategy, "
        "algorithmic framework, or statistical arbitrage signal that can be implemented.\n\n"
        "Respond strictly in JSON format with two keys:\n"
        "1. 'is_actionable_strategy': boolean (true if it proposes an implementable strategy, false if it is purely theoretical, macroeconomic, or high-level risk management without execution rules).\n"
        "2. 'reason': string (a 1-sentence justification for your choice)."
    )
    
    user_content = f"Title: {title}\nAbstract: {abstract}"
    
    # Construct the standard chat completion payload
    payload = client.chat.completions.create(
        model="llama-3.1-8b-instant",  # Ultra-fast, highly capable model for screening
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
        response_format={"type": "json_object"},
        temperature=0.0  # Zero temperature for deterministic classification
    )
    
    try:
        result = payload.choices[0].message.content
        # Parse the inner JSON content returned by the model
        # classification = json.loads(result)
        # return classification
        return result
        
    except Exception as e:
        print(f"Error screening paper '{title}': {e}")
        return {"is_actionable_strategy": False, "reason": "API classification failed."}

def filter_promising_papers(papers, api_key):
    """
    Iterates through a list of arXiv papers and retains only those flagged
    as actionable trading strategies.
    """
    filtered_papers = []
    
    print(f"Screening {len(papers)} papers for systematic trading strategies...\n")
    
    for paper in papers:
        evaluation = screen_abstract_with_groq(paper["title"], paper["summary"], api_key)
        evaluation = json.loads(evaluation)

        if evaluation["is_actionable_strategy"]:
            print(f"[PASS] {paper['title']}")
            print(f"Reason: {evaluation["reason"]}\n")
            
            # Enrich the paper dictionary with the screener's reasoning
            paper["screener_reason"] = evaluation["reason"]
            filtered_papers.append(paper)
        else:
            print(f"[FAIL] {paper['title']}")
            print(f"Reason: {evaluation["reason"]}\n")
            
    print(f"Screening complete. Retained {len(filtered_papers)} / {len(papers)} papers.")
    return filtered_papers
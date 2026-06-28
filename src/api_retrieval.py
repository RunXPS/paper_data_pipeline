import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET

def fetch_recent_quant_papers(start=0, max_results=10, target_date=None):
    """
    Fetches the newest quantitative finance papers from arXiv.
    If target_date (YYYY-MM-DD) is provided, only retrieves papers from that specific day.
    """
    # Target Categories: Trading, Portfolio Management, Statistics, Machine Learning
    categories = "cat:q-fin.TR OR cat:q-fin.PM OR cat:q-fin.ST OR cat:cs.LG"
    
    # Add date filtering natively to the arXiv query if provided
    if target_date:
        # arXiv requires the date format to be YYYYMMDDHHMM
        formatted_date = target_date.replace('-', '')
        date_query = f"submittedDate:[{formatted_date}0000 TO {formatted_date}2359]"
        # Combine the category filter and the date filter
        full_query = f"({categories}) AND {date_query}"
    else:
        full_query = categories
    
    # URL encode the search parameters so the API can read them
    search_query = urllib.parse.quote(full_query)
    
    # Construct the API URL
    url = f"http://export.arxiv.org/api/query?search_query={search_query}&sortBy=submittedDate&sortOrder=descending&start={start}&max_results={max_results}"
    
    if target_date:
        print(f"Fetching {max_results} papers for {target_date} (Starting at index {start})...")
    else:
        print(f"Fetching {max_results} newest papers (Starting at index {start})...")
        
    try:
        # Perform the HTTP GET request
        response = urllib.request.urlopen(url)
        xml_data = response.read().decode('utf-8')
        
        # Parse the XML response
        root = ET.fromstring(xml_data)
        
        # arXiv returns Atom 1.0 XML; we must map the namespace to find the tags
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        
        papers = []
        # Iterate through each paper entry in the XML
        for entry in root.findall('atom:entry', ns):
            title = entry.find('atom:title', ns).text.strip().replace('\n', ' ')
            summary = entry.find('atom:summary', ns).text.strip().replace('\n', ' ')
            published = entry.find('atom:published', ns).text
            link = entry.find('atom:id', ns).text
            
            papers.append({
                'title': title,
                'published': published,
                'summary': summary,
                'link': link
            })
            
        return papers

    except Exception as e:
        print(f"Failed to fetch papers: {e}")
        return []
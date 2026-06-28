import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET

# Update the function parameters to accept 'start'
def fetch_recent_quant_papers(start=0, max_results=10):
    categories = "cat:q-fin.TR OR cat:q-fin.PM OR cat:q-fin.ST"
    search_query = urllib.parse.quote(categories)
    
    # Inject the start parameter into the URL
    url = f"http://export.arxiv.org/api/query?search_query={search_query}&sortBy=submittedDate&sortOrder=descending&start={start}&max_results={max_results}"
    
    print(f"Fetching {max_results} papers (Starting at index {start})...")
    
    # Construct the API URL
    url = f"http://export.arxiv.org/api/query?search_query={search_query}&sortBy=submittedDate&sortOrder=descending&max_results={max_results}"
    
    print(f"Fetching newest papers...\n")
    
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
            # Clean up newline characters from the raw text
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

if __name__ == "__main__":
    # Test the function by grabbing the 5 most recent papers
    recent_papers = fetch_recent_quant_papers(max_results=5)
    
    for i, paper in enumerate(recent_papers, 1):
        print(f"[{i}] {paper['title']}")
        print(f"Date: {paper['published'][:10]}")
        print(f"URL: {paper['link']}")
        print(f"Abstract Preview: {paper['summary'][:200]}...\n")
        print("-" * 80)
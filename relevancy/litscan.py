import requests
from openai import OpenAI

from xml.etree import ElementTree as ET
from time import sleep
import random
import subprocess
# NCBI Entrez base URL
BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"

# Replace with your own NCBI API key (optional, but speeds up requests)
# API_KEY = "your_api_key"

# List of common User-Agents
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36"
]


def get_pmcids(term):
    url = f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?'
    url = url + f'db=pmc&term={term}[Title/Abstract]+AND+free+fulltext%5bfilter%5d&retmode=json'

    response = requests.get(url, ) #headers=headers, data=data)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Print the response
        json_response = response.json()
        arr = json_response['esearchresult']['idlist']

    else:
        # Print the error message
        print(f"Error: {response.status_code} - {response.text}")
        arr = []

    return arr


# Function to find similar papers using elink
def find_similar_papers(pmids, api_key=None):
    # Use the first PMID to find similar papers
    if not pmids:
        return []
    
    params = {
        'dbfrom': 'pubmed',
        'db': 'pubmed',
        'id': ','.join(pmids),
        'linkname': 'pubmed_pubmed',
        'retmode': 'xml',
        #'api_key': api_key
    }
    response = requests.get(f"{BASE_URL}elink.fcgi", params=params)
    tree = ET.fromstring(response.content)
    
    # Extract related article PMIDs
    similar_pmids = [id_tag.text for id_tag in tree.findall(".//LinkSetDb/Link/Id")]
    return similar_pmids

def get_pdf(pmcid):
    PMCLink="http://www.ncbi.nlm.nih.gov/pmc/articles/"
    #user_agent = "Mozilla/5.0 (Windows NT 5.2; rv:2.0.1) Gecko/20100101 Firefox/4.0.1"

    pdf_url = PMCLink + pmcid + '/pdf/'
    response = requests.get(pdf_url, ) #headers={'User-Agent': user_agent})

    wget_command = [f'/usr/bin/wget',
           f'--user-agent="Mozilla/5.0 (Windows NT 5.2; rv:2.0.1) Gecko/20100101 Firefox/4.0.1"',
           f'-q',
           f'-l1',
           f'--no-parent',
           f'-A.pdf',
           f'-O{pmcid}.pdf',
           pdf_url,
           # '2>/dev/null'
          ]
    # Execute the wget command
    try:
        subprocess.run(wget_command, check=True, ) #stderr=subprocess.DEVNULL)
        print(f"{pmcid}.pdf downloaded successfully!")
    except subprocess.CalledProcessError as e:
        print(" ".join(wget_command), "failed")
        print(f"Failed to download {pmcid} PDF. Error: {e}")

    return



import requests
import PyPDF2
import io

def is_pdf_relevant(pdf_filename, question):
    print(f'Asiking if {pdf_filename} is relevant')
    # Read the PDF content
    with open(pdf_filename, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        content = ""
        for page in pdf_reader.pages:
            content += page.extract_text()

    # Prepare the API request
    # Set OpenAI's API key and API base to use vLLM's API server.

    client = OpenAI(
        api_key="cmsc-35360",
        base_url="http://rbdgx2.cels.anl.gov:9999/v1"
    )

    # sampling_params = SamplingParams({"prompt_logprobs": 1, "logprobs": 1))
    chat_response = client.chat.completions.create(
        model="meta-llama/Meta-Llama-3.1-70B-Instruct",
        # logprobs=1,
        # top_logprobs=1,
        messages=[
            {"role": "user", "content": f"Given the following content from a scientific paper, \
            is it relevant to answering the question: '{question}'? \
            Please respond with 'Yes' or 'No' followed by a brief explanation.\n\nContent: {content[:2000]}..."},
        ],
        temperature=0.0,
        max_tokens=2056,
    )
    return chat_response


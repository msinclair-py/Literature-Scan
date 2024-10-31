import requests
import random
import subprocess
from openai import OpenAI
from xml.etree import ElementTree as ET
from time import sleep

# NCBI Entrez base URL
BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"

# Replace with your own NCBI API key (optional, but speeds up requests)
# API_KEY = "your_api_key"

def get_pmcids(term, retmax=20):
    sleep(1)
    url = f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?'
    url = url + f'db=pmc&term={term}[Title/Abstract]+AND+free+fulltext%5bfilter%5d&retmode=json&retmax={retmax}'

    response = requests.get(url, ) #headers=headers, data=data)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Print the response
        print(f'The response is {response}')
        json_response = response.json()
        if 'esearchresult' in json_response and 'idlist' in json_response['esearchresult']:
            arr = json_response['esearchresult']['idlist']
        else:
            arr = []

    else:
        # Print the error message
        print(f"Error: {response.status_code} - {response.text}")
        arr = []

    return arr


# Function to find similar papers using elink
def find_similar_papers(pmid, api_key=None):
    sleep(1)
    
    params = {
        'dbfrom': 'pubmed',
        'db': 'pubmed',
        'id': pmid,
        'linkname': 'pubmed_pubmed',
        'retmode': 'xml',
        #'api_key': api_key
    }
    similar_pmids = []
    try:
    # Check if the response content is empty
        response = requests.get(f"{BASE_URL}elink.fcgi", params=params)
        if not response.content:
            raise ValueError("Empty response content")

        # Parse the XML content
        # print(f'parsing response {response.content}')
        tree = ET.fromstring(response.content)
        # Extract related article PMIDs
        similar_pmids = [id_tag.text for id_tag in tree.findall(".//LinkSetDb/Link/Id")]

    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
    except ET.ParseError as e:
        print(f"XML parsing error: {e}")

    return similar_pmids

def get_pdf(pmcid):
    if os.path.exists(f'{pmcid}.pdf'):
        return

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
import os

def is_pdf_relevant(pdf_filename, question):

    print(f'Asking if {pdf_filename} is relevant')
    if os.stat(pdf_filename).st_size == 0:
        print(f"The file {pdf_filename} is empty. It is being deleted")
        os.remove(pdf_filename)
        return
    with open(pdf_filename, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        content = ""
        for page in pdf_reader.pages:
            content += page.extract_text()


    client = OpenAI(
        api_key="cmsc-35360",
        base_url="http://rbdgx2.cels.anl.gov:9999/v1"
    )

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


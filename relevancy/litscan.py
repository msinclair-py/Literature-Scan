import requests
import random
import subprocess
from openai import OpenAI
from xml.etree import ElementTree as ET
from time import sleep
import json
import requests
import PyPDF2
import io
import os

# NCBI Entrez base URL
BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"

# Replace with your own NCBI API key (optional, but speeds up requests)
# API_KEY = "your_api_key"

class Config:
    """Configuration class to manage API endpoints and settings"""
    
    def __init__(self):
        # OpenAI Settings
        self.openai_api_key = "cmsc-35360"
        self.openai_base_url = "http://localhost:9999/v1"
        self.openai_model = "llama31-405b-fp8"

        # NCBI Settings
        self.retmax = 20

def get_pmcids(term, retmax=Config.retmax):
    """
    Retrieves PubMed Central IDs (PMCIDs) for articles matching a search term.

    This function searches PubMed Central using the NCBI E-utilities API to find articles
    that contain the given term in either their title or abstract. It only returns articles
    that have free full text available.

    Args:
        term (str): The search term to look for in article titles and abstracts
        retmax (int, optional): Maximum number of results to return. Defaults to 20.

    Returns:
        list: A list of PMCIDs as strings. Returns an empty list if no results are found
              or if the API request fails.

    Note:
        - Includes a 1 second delay to comply with NCBI E-utilities usage guidelines
        - Only returns articles with free full text access
        - Searches both title and abstract fields
    """
    sleep(1)
    url = f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?'
    
    url = url + f'db=pmc&term={term}[Title/Abstract]+AND+free+fulltext%5bfilter%5d&retmode=json&retmax={retmax}'
    # print(f'get_pmcids url: {url}')
    response = requests.get(url, ) #headers=headers, data=data)

    if response.status_code == 200:
        # print(f'The response is {response}')
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

def get_pmcids_for_term_and_partner(term, partner, title_only=False, abstract_only=False, retmax=Config.retmax):
    """
    Retrieves PubMed Central IDs (PMCIDs) for articles containing both search terms.

    This function searches PubMed Central using the NCBI E-utilities API to find articles
    that contain both the given terms. The search can be restricted to title only,
    abstract only, or both title and abstract (default).

    Args:
        term (str): The first search term to look for
        partner (str): The second search term to look for
        title_only (bool, optional): If True, search only in article titles. Defaults to False.
        abstract_only (bool, optional): If True, search only in article abstracts. Defaults to False.
        retmax (int, optional): Maximum number of results to return. Defaults to 20.

    Returns:
        list: A list of PMCIDs as strings that mat. Returns an empty list if no results are found
              or if the API request fails.

    Note:
        - Includes a 1 second delay to comply with NCBI E-utilities usage guidelines
        - Only returns articles with free full text access
        - If neither title_only nor abstract_only is True, searches both fields
    """
    sleep(1)
    if title_only:
        term_query = f'({term}[Title] AND {partner}[Title])'
    elif abstract_only:
        term_query = f'({term}[Abstract]) AND {partner}[Abstract])'
    else:
        term_query = f'(({term}[Title] OR {term}[Abstract]) AND ({partner}[Title] OR {partner}[Abstract]))'
    
    url = (f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?'
           f'db=pmc&'
           f'term={term_query}'
           f'+AND+free+fulltext%5bfilter%5d&'
           f'retmode=json&'
           f'retmax={retmax}')
    
    # print(f'get_pmcids_for_term_and_partner url: {url}')
    response = requests.get(url)
    if response.status_code == 200:
        json_response = response.json()
        if 'esearchresult' in json_response and 'idlist' in json_response['esearchresult']:
            arr = json_response['esearchresult']['idlist']
        else:
            arr = []
    else:
        print(f"Error: {response.status_code} - {response.text}")
        arr = []
    return arr

def get_pdf(pmcid):
    """
    Downloads a PDF article from PubMed Central given its PMCID.

    This function attempts to download a PDF article from PubMed Central using wget.
    If the PDF already exists locally, it skips the download.

    Args:
        pmcid (str): The PubMed Central ID of the article to download

    Returns:
        None

    Note:
        - Includes a 1 second delay to comply with NCBI usage guidelines
        - Uses wget to download the PDF file
        - Saves the PDF with filename {pmcid}.pdf in the current directory
        - Requires wget to be installed on the system
        - Will attempt to find wget in common installation locations
    """

    if os.path.exists(f'{pmcid}.pdf'):
        return
    
    sleep(1)

    PMCLink="http://www.ncbi.nlm.nih.gov/pmc/articles/"
    #user_agent = "Mozilla/5.0 (Windows NT 5.2; rv:2.0.1) Gecko/20100101 Firefox/4.0.1"

    pdf_url = PMCLink + pmcid + '/pdf/'
    response = requests.get(pdf_url, ) #headers={'User-Agent': user_agent})

    wget_path = None
    possible_paths = ['/usr/bin/wget', '/opt/homebrew/bin/wget', '/usr/local/bin/wget']
    
    for path in possible_paths:
        if os.path.exists(path):
            wget_path = path
            break
    
    if wget_path is None:
        wget_path = '/usr/bin/wget'

    wget_command = [wget_path,
           f'--user-agent="Mozilla/5.0 (Windows NT 5.2; rv:2.0.1) Gecko/20100101 Firefox/4.0.1"',
           f'-q',
           f'-l1',
           f'--no-parent',
           f'-A.pdf',
           f'-O{pmcid}.pdf',
           pdf_url,
          ]
    
    try:
        subprocess.run(wget_command, check=True, ) #stderr=subprocess.DEVNULL)
        # print(f"{pmcid}.pdf downloaded successfully!")

    except subprocess.CalledProcessError as e:
        print(" ".join(wget_command), "failed")
        print(f"Failed to download {pmcid} PDF. Error: {e}")

    return





# tools
def is_pdf_relevant(pdf_filename, question):

    try:
        if os.stat(pdf_filename).st_size == 0:
            print(f"The file {pdf_filename} is empty. It is being deleted")
            os.remove(pdf_filename)
            return None
    except FileNotFoundError:
        print(f"The file {pdf_filename} does not exist")
        return None

    with open(pdf_filename, 'rb') as file:
        
        pdf_reader = PyPDF2.PdfReader(file)
        content = ""
        for page in pdf_reader.pages:
            content += page.extract_text()


    client = OpenAI(
        api_key=OPENAI_API_KEY,
        base_url=OPENAI_BASE_URL
    )

    chat_response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "user", "content": f"Given the following content from a scientific paper, \
            is it relevant to answering the question: '{question}'? \
            Please respond with 'Yes' or 'No' followed by a brief explanation.\n\nContent: {content[:2000]}..."},
        ],
        temperature=0.0,
        max_tokens=2056,
    )
    return chat_response

def get_string_id(protein_name):
    """
    Retrieve publications related to a protein target from the STRING database.
    
    Args:
        protein_name (str): Name of the protein target
        
    Returns:
        list: List of publication details (PMIDs, titles, etc.)
    """
    # STRING API base URL
    string_api_url = "https://string-db.org/api"
    
    # First get the STRING protein ID
    
    #protein_query_url = f"{string_api_url}/json/get_string_ids?identifiers={protein_name}&species=9606"  # 9606 is human
    
    protein_query_url ="https://string-db.org/api/tsv/get_string_ids?identifiers={protein_name}"
    # RTCBS%0D%0ANSUN2%0D%0AALKBH1"

    your_identifiers = protein_name
    output_format = "json"
    optional_parameters = ""
    protein_query_url = f"https://string-db.org/api/{output_format}/get_string_ids?identifiers={your_identifiers}&{optional_parameters}"
    # print(f'protein_query_url: {protein_query_url}')

    try:
        # Get protein ID from STRING
        response = requests.get(protein_query_url)
        # print(f'response: {response}')
        # print(f'response.content: {response.content}')

        response.raise_for_status()
        protein_data = response.json()
        print(f'length of protein_data: {len(protein_data)}')
        
        if not protein_data:
            print(f"No STRING ID found for protein: {protein_name}")
            return []
            
        string_id = protein_data[0]['stringId']
        
    except requests.exceptions.RequestException as e:
        print(f"Error accessing STRING database: {e}")
        return []
        
    return string_id

def get_string_publications_by_id(string_id):
    """
    TODO: this is not implemented yet

    Get publications for a protein from STRING using its STRING ID
    
    Args:
        string_id (str): STRING ID for the protein
        
    Returns:
        list: List of publications from STRING
    """
    output_format = "json"
    optional_parameters = ""
    publications_url = "UNKNOWN"
    # print(f'publications_url: {publications_url}')

    try:
        pub_response = requests.get(publications_url)
        pub_response.raise_for_status()
        publications = pub_response.json()
        print(f'length of publications: {len(publications)}')
  
    except requests.exceptions.RequestException as e:
        print(f"Error accessing STRING database: {e}")
        return []
    return pub_response.json()

def get_string_functional_annotation(protein_name):
    """
    Get functional annotations for a protein from STRING database
    
    Args:
        protein_name (str): Name of the protein to query
        
    Returns:
        list: List of functional annotations from STRING
    """
    output_format = "json"
    optional_parameters = ""
    functional_url = f"https://string-db.org/api/{output_format}/functional_annotation?identifiers={protein_name}&{optional_parameters}"
    # print(f'functional_url: {functional_url}')

    try:
        response = requests.get(functional_url)
        response.raise_for_status()
        functional_data = response.json()
        print(f'length of functional_data: {len(functional_data)}')

        if not functional_data:
            print(f"No functional annotations found for protein: {protein_name}")
            return []
            
        return functional_data
        
    except requests.exceptions.RequestException as e:
        print(f"Error accessing STRING database: {e}")
        return []

def get_string_interaction_partners(protein_name, limit=10):
    """
    Get interaction partners for a protein from STRING database
    
    Args:
        protein_name (str): Name of the protein to query
        
    Returns:
        list: List of interaction partners from STRING
    """
    output_format = "json"
    optional_parameters = f"limit={limit}"
    interaction_url = f"https://string-db.org/api/{output_format}/interaction_partners?identifiers={protein_name}&{optional_parameters}"
    # print(f'interaction_url: {interaction_url}')

    try:
        response = requests.get(interaction_url)
        response.raise_for_status()
        interaction_partners = response.json()
        print(f'length of interaction_partners: {len(interaction_partners)}')
        
        if not interaction_partners:
            print(f"No interaction partners found for protein: {protein_name}")
            return []
            
        return interaction_partners
        
    except requests.exceptions.RequestException as e:
        print(f"Error accessing STRING database: {e}")
        return []

def print_detailed(json_data):
    # Print detailed structure information
    print("\nDetailed functional data structure:")
    for i, item in enumerate(json_data):
        print(f"\nItem {i}:")
        for key, value in item.items():
            print(f"  {key}: {type(value)}")
            if isinstance(value, (list, dict)):
                print(f"    Content: {json.dumps(value, indent=4)}")
            else:
                print(f"    Content: {value}")

if __name__ == "__main__":

    # print(get_string_publications("RTCB_HUMAN"))

    functional_data = get_string_functional_annotation("RTCB_HUMAN")
    for i, item in enumerate(functional_data):
        print(f'item {i}: {item["category"]}\t{item["description"]}')


    interaction_data = get_string_interaction_partners("RTCB_HUMAN")
    for i, item in enumerate(interaction_data):
            #print(f'item {i}: {item}')
            print(f'item {i}: {item["preferredName_B"]}')


    for target, partner in ([['WRN', 'DNA2']]):
        pmids = get_pmcids_for_term_and_partner(target, partner, title_only=True)
        print(f'{target} AND {partner} (title only): {pmids}, {len(pmids)}')
        sleep(1)
        pmids = get_pmcids_for_term_and_partner(target, partner, abstract_only=True)
        print(f'{target} AND {partner} (abstract only): {pmids}, {len(pmids)}')
        sleep(1)
        pmids = get_pmcids_for_term_and_partner(target, partner)
        print(f'{target} AND {partner} (title and abstract): {pmids}, {len(pmids)}')
        sleep(1)



    print(is_pdf_relevant("10069449.pdf", "What is the role of RTCB in DNA repair?"))

from configs import LLMConfig, LitScanConfig
import json
from openai import OpenAI
import os
import pymupdf
import requests
import subprocess
import sys
import tiktoken
from time import sleep
from typing import Dict, List, Union
from xml.etree import ElementTree as ET

# Add the directory containing the current script to Python path
# Or to get the parent directory (if modules are one level up)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class Logger:
    def __init__(self, config=LLMConfig):
        import logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers = [
                logging.FileHandler(config.logfile)
            ]
        )

        self.log = logging.getLogger('litscan')

class LitScanner:
    """
    Base literature scanner. Capable of working with local PDF files only. See 
    child classes for scraping PMC/STRING-DB papers.
    """
    def __init__(self, logger=Logger, pdfs=None, outdir='.', 
                 chunk_size=2048*8, chunk_overlap=2048*4, 
                 relevancy_cutoff: float=.1):
        self.logger = logger.log
        self.pdfs = pdfs
        self.outdir = outdir
        self.size = chunk_size
        self.overlap = chunk_overlap
        self.relevancy_cutoff = relevancy_cutoff

    def get_pdf(self, pmcid):
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
    
        if os.path.exists(f'{self.outdir}/{pmcid}.pdf'):
            self.logger.info(f'{self.outdir}/{pmcid}.pdf already exists')
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
               f'--waitretry=1',
               f'-t 3',
               f'-q',
               f'-l1',
               f'--no-parent',
               f'-A.pdf',
               f'-O{self.outdir}/{pmcid}.pdf',
               pdf_url,
              ]
        
        try:
            subprocess.run(wget_command, check=True, ) #stderr=subprocess.DEVNULL)
            self.logger.info(f"{pmcid}.pdf downloaded successfully!")
        except subprocess.CalledProcessError as e:
            self.logger.info(" ".join(wget_command), "failed")
            self.logger.warn(f"Failed to download {pmcid} PDF. Error: {e}")
    
    def is_pdf_relevant(self, pdf_filename, questions, weights):
        pdf = os.path.join(self.outdir, pdf_filename)
        try:
            if os.stat(pdf).st_size == 0:
                os.remove(pdf)
                return None
        except FileNotFoundError:
            self.logger.info(f"The file {pdf} does not exist")
            return None

        # Extract text from PDF
        self.logger.info(f'extracting text from {pdf}')
        content = self.extract_pdf_text(pdf)
        if not content:
            return None
        
        # Split content into chunks
        self.logger.info(f'splitting content into chunks')
        chunks = self._chunk_text(content, chunk_size=self.size, overlap_tokens=self.overlap)
        
        return self.query_relevance(chunks, questions, weights)

    def query_relevance(self, chunks, questions, weights=None) -> Dict:
        """
        Queries whether or not any of the chunks of text have relevance to
        our supplied question(s). Scores based on user-supplied weights or
        uniform weights if not provided. In multi-question prompts, leverages
        prompt caching for a 50% discount on GPT-4o for each additional
        question.
        """
        # Process each chunk
        total_chunks = len(chunks)
        chunk_responses = [[] for _ in range(total_chunks)]
        relevant_answers = [[None for c in range(total_chunks)] for _ in range(len(questions))]
        scores = [0 for _ in range(total_chunks)]
        print('\n'.join(questions))
        for i, chunk in enumerate(chunks):
            try:
                responses = self.ask_llm_about_relevance(chunk, questions)

                for j, response in enumerate(responses):
                    if response and response.choices:
                        answer = response.choices[0].message.content
                        print(answer) # only prints if we have an answer
                        is_chunk_relevant = answer.lower().startswith('yes')
                        
                        if is_chunk_relevant:
                            if weights is None:
                                scores[i] += 1 / len(questions)
                            else:
                                scores[i] += weights[j] / sum(weights)
                            
                            try:
                                relevant_answers[i][j] = [answer]
                            except IndexError: # if only 1 chunk total
                                relevant_answers[j] = [answer]

                        chunk_responses[i].append(response)

            except Exception as e:
                self.logger.warn(f"Error processing chunk {i+1}: {e}")
                continue
        
        # If no valid responses, return None
        if not any(chunk_responses):
            return None
    
        # Determine overall relevance
        if any([score > self.relevancy_cutoff for score in scores]):
            is_relevant = True
        elif sum(scores) > self.relevancy_cutoff:
            is_relevant = True
        else:
            is_relevant = False
            results = {'score': 0.0, 'response': 'No response'}
            
        # Create a combined response
        if is_relevant:
            results = {'score': scores[i]}

            As, Qs = [], []
            for i, answer in enumerate(relevant_answers):
                for j, ans in enumerate(answer):
                    if ans is not None:
                        As.append(ans)
                        Qs.append(questions[j])

            if len(As) > 1: # multiple answers must be synthesized together
                response = self.synthesize_response(As, Qs)
                synth_response = response

                if synth_response is None: # failed to synthesize an answer
                    synth_response = '\n'.join(As)

                results.update(
                    {
                        'response': synth_response
                    }
                )
            elif As: # only one answer
                results.update(
                    {
                        'response': As[0]
                    }
                )
            else: # no answers
                results.update(
                    {
                        'response': 'No response'
                    }
                )

        return results

    def ask_llm_about_relevance(self, content, questions):
        """
        Asks the LLM whether a given content is relevant to answering a specific question.
    
        This function uses the configured LLM (Large Language Model) to evaluate whether a piece of
        text content is relevant for answering a specific question. It prompts the LLM to provide
        a Yes/No response with a brief explanation.
    
        Args:
            content (str): The text content to analyze (typically from a scientific paper)
            question (str): The question to evaluate relevance against
    
        Returns:
            ChatCompletion: The response from the LLM containing relevance assessment.
                           The response will include a Yes/No answer followed by a brief explanation.
    
        Example:
            >>> content = "This paper discusses the role of RTCB in RNA ligation..."
            >>> question = "What is the role of RTCB in DNA repair?"
            >>> response = ask_llm_about_relevance(content, question)
            >>> print(response.choices[0].message.content)
            "No. This paper focuses on RTCB's role in RNA ligation rather than DNA repair."
    
        Note:
            - The function truncates the content to the first 2000 characters to stay within
              typical LLM token limits
            - Uses temperature=0.0 for more consistent, deterministic responses
            - Configured to use the LLM settings from LitScanConfig
        """
        self.logger.info(f'establishing client on base_url: {self.config.openai_base_url}')
        client = OpenAI(
            api_key=self.config.openai_api_key,
            base_url=self.config.openai_base_url
        )
    
        self.logger.info(f'requesting chat.completion')
        responses = []
        for question in questions:
            chat_response = client.chat.completions.create(
                model=self.config.openai_model,
                messages=[
                    {'role': 'user', 'content': f'Please read the following content from a scientific \
                     paper and then answer a question. Content: {content} ... \n\n Is this passage relevant \
                     to answering the question: "{question}"? Please respond with "Yes" or "No" followed \
                     by a brief explanation.'}
                    #{"role": "user", "content": f"Given the following content from a scientific paper, \
                    #is it relevant to answering the question: '{question}'? \
                    #Please respond with 'Yes' or 'No' followed by a brief explanation.\n\nContent: {content}..."},
                ],
                temperature=0.0,
            )

            responses.append(chat_response)
            sleep(1)

        return responses

    def synthesize_response(self, responses, questions):
        self.logger.info(f'establishing client on base_url: {self.config.openai_base_url}')
        client = OpenAI(
            api_key=self.config.openai_api_key,
            base_url=self.config.openai_base_url
        )
    
        self.logger.info(f'requesting chat.completion')
    
        content = []
        for question, response in zip(questions, responses):
            if 'No response' in response or response == None:
                continue
            else:
                content.append(f'Question: {question}\nResponse: {response}\n')

        content = '\n'.join(content)
        
        chat_response = client.chat.completions.create(
            model=self.config.openai_model,
            messages=[
                {'role': 'user', 'content': f'Please read the following content \
                 which consists of pairs of questions and responses regarding a \
                 scientific paper. Combine these responses into a single summary \
                 which still answers all questions provided. Content:\n{content} ...'}
            ],
            temperature=0.0,
        )

        try:
            return chat_response.choices[0].message.content
        except AttributeError:
            return None
    
    @staticmethod
    def _chunk_text(text: str, chunk_size=2048*32, overlap_tokens=2048*16) -> list[str]:
        """Split text into overlapping chunks based on token count"""
        chunks = []
        tokenizer = tiktoken.encoding_for_model("gpt-4o")
        tokens = tokenizer.encode(text)
    
        start = 0
        while start < len(tokens):
            # Get chunk of tokens
            end = start + chunk_size
            chunk_tokens = tokens[start:end]
    
            # Convert chunk tokens back to text
            chunk_text = tokenizer.decode(chunk_tokens)
            chunks.append(chunk_text)
    
            # Move start position, accounting for overlap
            start = end - overlap_tokens
    
        return chunks
    
    def extract_pdf_text(self, pdf_filename):
        """
        Extracts text content from a PDF file.
    
        Args:
            pdf_filename (str): Path to the PDF file
    
        Returns:
            str: Extracted text content from the PDF, or None if extraction fails
        """
        try:
            doc = pymupdf.open(pdf_filename)
            content = ''
            for page in doc:
                content += page.get_text()

            return content if content else None

        except Exception as e:
            self.logger.warn(f"Error extracting text from {pdf_filename}: {e}")
            return None
        
    def extract_html_text(self, html_content):
        """
        Extracts text content from HTML string.
    
        Args:
            html_content (str): HTML content to extract text from
    
        Returns:
            str: Extracted text content from the HTML, or None if extraction fails
        """
        try:
            from bs4 import BeautifulSoup
            
            # Parse HTML and extract text
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
                
            # Get text and normalize whitespace
            content = soup.get_text(separator=' ')
            content = ' '.join(content.split())
            
            return content if content else None
        except Exception as e:
            self.logger.warn(f"Error extracting text from HTML: {e}")
            return None


class PMCScanner(LitScanner):
    def __init__(self, logger: Logger, cfg: LitScanConfig, 
                 outdir: str='papers', chunk_size: int=2048*16,
                 chunk_overlap: int=2048*8, relevancy_cutoff: float=.1):
        super(PMCScanner, self).__init__(logger, None, outdir, chunk_size, 
                                         chunk_overlap, relevancy_cutoff)
        self.config = cfg

    def get_ids(self, term, retmax=None):
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
        
        # Build URL parameters
        db = "pmc"
        search_term = f"{term}[Title/Abstract]"
        filter_param = "" # "+AND+free+fulltext%5bfilter%5d" 
        return_mode = "json"
        
        if retmax is None:
            retmax = self.config.retmax
            
        # Combine into final URL
        url = url + f'db={db}&term={search_term}{filter_param}&retmode={return_mode}&retmax={retmax}'
        self.logger.info(f'get_pmcids url: {url}')
        
        response = requests.get(url, ) #headers=headers, data=data)
    
        if response.status_code == 200:
            json_response = response.json()
            if 'esearchresult' in json_response and 'idlist' in json_response['esearchresult']:
                arr = json_response['esearchresult']['idlist']
            else:
                arr = []
    
        else:
            self.logger.warn(f"Error: {response.status_code} - {response.text}")
            arr = []
    
        return arr
    
    def get_ids_by_author(self, author, retmax=None):
        """
        Retrieves PubMed Central IDs (PMCIDs) for articles by a specific author.
    
        This function searches PubMed Central using the NCBI E-utilities API to find articles
        published by the specified author.
    
        Args:
            author (str): The author name to search for (e.g., "Smith J" or "Smith JA")
            retmax (int, optional): Maximum number of results to return. Defaults to 20.
    
        Returns:
            list: A list of PMCIDs as strings. Returns an empty list if no results are found
                  or if the API request fails.
    
        Note:
            - Includes a 1 second delay to comply with NCBI E-utilities usage guidelines
            - Author name format should match PubMed's format (typically "Last FM")
        """
        sleep(1)
        url = f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?'
        #url = url + f'db=pmc&term={author}[Author]+AND+free+fulltext[filter]&retmode=json&retmax={retmax}'
        if retmax is None:
            retmax = self.config.retmax

        url = url + f'db=pmc&term={author}[Author]&retmode=json&retmax={retmax}'
        response = requests.get(url)
    
        if response.status_code == 200:
            json_response = response.json()
            if 'esearchresult' in json_response and 'idlist' in json_response['esearchresult']:
                arr = json_response['esearchresult']['idlist']
            else:
                arr = []
        else:
            self.logger.warn(f"Error: {response.status_code} - {response.text}")
            arr = []
    
        return arr
    
    def get_ids_for_term_and_partner(self, term, partner, 
                                     title_only=False, abstract_only=False, 
                                     retmax=None):
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
        
        if retmax is None:
            retmax = self.config.retmax

        url = (f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?'
               f'db=pmc&'
               f'term={term_query}'
               # f'+AND+free+fulltext%5bfilter%5d'
               f'&retmode=json&'
               f'retmax={retmax}')
        
        response = requests.get(url)
        if response.status_code == 200:
            json_response = response.json()
            if 'esearchresult' in json_response and 'idlist' in json_response['esearchresult']:
                arr = json_response['esearchresult']['idlist']
            else:
                arr = []
        else:
            self.logger.warn(f"Error: {response.status_code} - {response.text}")
            arr = []
        return arr


class StringDBScanner(LitScanner):
    def __init__(self, logger=Logger, cfg=LitScanConfig):
        super().__init__(logger)
        self.config = cfg

    def get_ids(self, protein_name, output_format='json', optional_parameters=''):
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
    
        your_identifiers = protein_name
        protein_query_url = f"https://string-db.org/api/{output_format}/get_string_ids?identifiers={your_identifiers}&{optional_parameters}"
    
        try:
            # Get protein ID from STRING
            response = requests.get(protein_query_url)
    
            response.raise_for_status()
            protein_data = response.json()
            
            if not protein_data:
                return []
                
            string_id = protein_data[0]['stringId']
            
        except requests.exceptions.RequestException as e:
            self.logger.warn(f"Error accessing STRING database: {e}")
            return []
            
        return string_id
    
    def get_publications_by_id(self, string_id):
        """
        TODO: this is not implemented yet
    
        Get publications for a protein from STRING using its STRING ID
        
        Args:
            string_id (str): STRING ID for the protein
            
        Returns:
            list: List of publications from STRING
        """
        raise NotImplementedError('This method is not yet implemented!')
        output_format = "json"
        optional_parameters = ""
        publications_url = "UNKNOWN"
    
        try:
            pub_response = requests.get(publications_url)
            pub_response.raise_for_status()
            publications = pub_response.json()
      
        except requests.exceptions.RequestException as e:
            logger.warn(f"Error accessing STRING database: {e}")
            return []
        return pub_response.json()
    
    def get_string_functional_annotation(self, protein_name):
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
    
        try:
            response = requests.get(functional_url)
            response.raise_for_status()
            functional_data = response.json()
    
            if not functional_data:
                return []
                
            return functional_data
            
        except requests.exceptions.RequestException as e:
            self.logger.warn(f"Error accessing STRING database: {e}")
            return []
    
    def get_string_interaction_partners(self, protein_name, limit=10):
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
    
        try:
            response = requests.get(interaction_url)
            response.raise_for_status()
            interaction_partners = response.json()
            
            if not interaction_partners:
                return []
                
            return interaction_partners
            
        except requests.exceptions.RequestException as e:
            self.logger.warn(f"Error accessing STRING database: {e}")
            return []


if __name__ == "__main__":
    """
    # get functional annotations
    functional_data = get_string_functional_annotation("WRN")
    for i, item in enumerate(functional_data):
        print(f'item {i}: {item["category"]}\t{item["description"]}')

    # get interaction partners
    interaction_data = get_string_interaction_partners("WRN")
    for i, item in enumerate(interaction_data):
        print(f'item {i}: {item["preferredName_B"]}')

    # get pmcids
    pmids = []
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

    # get pdfs
    print("---------------get pdfs-----------------")
    for pmcid in pmids:
        print(f"pmcid: {pmcid}")
        get_pdf(pmcid)

    # ask llm about relevance
    print("---------------ask llm about relevance-----------------")
    for pmcid in pmids:
        print(f"is {pmcid} relevant?")
        response = is_pdf_relevant(f"{pmcid}.pdf", "What is the role of WRN in Cancer?")
        print(f'{response.choices[0].message.content}' if response else "No response")
    print("--------------------------------")
    """ 

from litscan import get_string_interaction_partners
from litscan import get_pmcids
from litscan import get_pmcids_for_term_and_partner
from litscan import get_pdf
from litscan import is_pdf_relevant

import os
from time import sleep
from typing import List

import logging

import argparse

# Get the default log filename by changing .py to .log
default_logfile = os.path.splitext(__file__)[0] + '.log'

# Initialize the parser
parser = argparse.ArgumentParser(description="A simple download and relevancy testing program.")

parser.add_argument("--template", type=str, help="The question you want to ask.",
        default="What is the role of the gene {}?")
parser.add_argument("--terms", nargs="+", help="List of items", 
        default=["WHSC1", "RTCB"]) # , "WRN", "P2X7", "NLRP3", "CSF1R", "ALKBH1", "NMNAT2", "NSUN2", "RTCB"])
parser.add_argument("--retmax", type=int, default=20, help="The maximum number of papers to download.")
parser.add_argument("--no_delete", action="store_true", help="If set, do not delete pdf if not relevant")
parser.add_argument("--get_partners", action="store_true", default=False, help="Use partner data")
parser.add_argument("--logfile", type=str, 
                   default=default_logfile,
                   help="Path to the log file (default: %(default)s)")


class Config:
    """Configuration settings for the literature scanning application."""

    # Partner interaction settings
    PARTNER_LIMIT = 50
    PARTNER_SCORE_THRESHOLD = 0.925

# Parse arguments
args     = parser.parse_args()
retmax   = args.retmax
template = args.template
terms    = args.terms
no_delete   = args.no_delete # defaults to False if not set

get_partners = args.get_partners
logfile = args.logfile

# For testing
get_partners = True

# Configure logging to both file and console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(logfile),
        # logging.StreamHandler()  # This will continue logging to console
    ]
)
logger = logging.getLogger(__name__)
logger.info(f'Logging to file: {logfile}')
logger.info(f'Arguments: {args}')



# Add this helper function after the argument parsing and before main()
def process_relevancy_check(pmid, question, delete_if_no=False):
    """
    Process a relevancy check for a PDF and return the score (-1 for no, 1 for yes).
    
    Args:
        pmid: The PMID of the paper to check
        question: The question to ask about the paper
        delete_if_no: Whether to delete the PDF if the answer is no
    
    Returns:
        int: 1 if relevant, -1 if not relevant, 0 if error
    """
    chat_response = is_pdf_relevant(f"{pmid}.pdf", question)
    if chat_response is None:
        logger.info(f"chat response {chat_response} does not contain choices")
        return 0
    
    answer = chat_response.choices[0].message.content
    logger.info(f'Is {pmid}.pdf relevant to the question: {question}')
    logger.info(f'Answer: {answer}')
    
    is_relevant = not answer.lower().startswith('no')
    if not is_relevant and delete_if_no:
        logger.info(f'removing {pmid}.pdf')
        os.remove(f'{pmid}.pdf')
    
    return 1 if is_relevant else -1

def get_relevant_partners(term: str) -> List[str]:
    """Get relevant interaction partners for a given term above a score threshold."""
    partners = []
    partner_data = get_string_interaction_partners(term, limit=Config.PARTNER_LIMIT)
    
    for i, item in enumerate(partner_data):
        partner = item["preferredName_B"]
        logger.info(f'{i}\t{item["preferredName_A"]}\t{item["preferredName_B"]}\t{item["score"]}')
        
        if item["score"] > Config.PARTNER_SCORE_THRESHOLD:
            partners.append(partner)
    
    return partners

def process_partner_relevancy(pmid: str, term: str, matching_partner: str, template: str, no_delete: bool) -> int:
    """
    Process relevancy checks for a paper containing partner interactions.
    
    Args:
        pmid: The PMID of the paper to check
        term: The main gene term
        matching_partner: The partner gene to check
        template: Question template to use
        no_delete: If True, keep PDFs even if not relevant
    
    Returns:
        int: Score indicating relevancy (3=fully relevant with interactions, 
             2=relevant genes, -2=irrelevant genes)
    """
    score = 0

    # Check relevancy for main term
    question1 = template.format(term)
    score += process_relevancy_check(pmid, question1)

    # Check relevancy for partner
    question2 = template.format(matching_partner)
    score += process_relevancy_check(pmid, question2)

    logger.info(f'score {score}')
    if (score == -2) and (not no_delete):
        logger.info(f'removing {pmid}.pdf')
        os.remove(f'{pmid}.pdf')

    # Check for interactions if both genes are relevant
    if score == 2:
        question3 = f"What, if any, physical interactions occur between {term} and {matching_partner}"
        score += process_relevancy_check(pmid, question3)

    if score != 3 and not no_delete:
        if os.path.exists(f'{pmid}.pdf'):
            logger.info(f'removing {pmid}.pdf')
            os.remove(f'{pmid}.pdf')

    return score

# In process_pdf_relevancy, replace the matching code block with:
    if matching_partner:
        return process_partner_relevancy(pmid, term, matching_partner, template, no_delete)

def process_pdf_relevancy(pmid: str, term: str, get_partners: bool, template: str, 
                         no_delete: bool, partner_dict: dict = None) -> int:
    """
    Process a PDF file to determine its relevancy based on specified criteria.
    
    Args:
        pmid: The PMID of the paper to check
        term: The gene term being searched
        get_partners: Whether to check for partner interactions
        template: The question template to use
        no_delete: If True, keep PDFs even if not relevant
        partner_dict: Dictionary mapping partners to their PMIDs (required if get_partners=True)
    
    Returns:
        int: The relevancy score (3 for fully relevant with interactions, 2 for relevant genes,
             -2 for irrelevant genes, or None if no partner processing was done)
    """
    if not os.path.exists(f'{pmid}.pdf'):
        logger.info(f'file {pmid}.pdf does not exist')
        return None # should not happen, but just in case, should it return 0?

    if not get_partners:
        question = template.format(term)
        score = process_relevancy_check(pmid, question, delete_if_no=not no_delete)
        return score

    # Partner processing
    matching_partner = None
    results = []
    for p, pmid_list in partner_dict.items():
        if pmid in pmid_list:
            matching_partner = p
            score = 0

            # Check relevancy for main term
            question1 = template.format(term)
            score += process_relevancy_check(pmid, question1)

            # Check relevancy for partner
            question2 = template.format(matching_partner)
            score += process_relevancy_check(pmid, question2)

            logger.info(f'score {score}')
            if (score == -2) and (not no_delete):
                logger.info(f'removing {pmid}.pdf')
                os.remove(f'{pmid}.pdf')

            # Check for interactions if both genes are relevant
            if score == 2:
                question3 = f"What, if any, physical interactions occur between {term} and {matching_partner}"
                score += process_relevancy_check(pmid, question3)

            if score != 3 and not no_delete:
                if os.path.exists(f'{pmid}.pdf'):
                    logger.info(f'removing {pmid}.pdf')
                    os.remove(f'{pmid}.pdf')
            # Store results for this partner
            results.append((term, matching_partner, pmid, score))
            
    return results

def main():
    results = []
    for term in terms:
        pmids = [] 
        partner_dict = {}  # key is partner, value is list of unvalidated PMIDs.

        # Part 1: Get pmids for term AND each partner
        if get_partners == True:
            partners = get_relevant_partners(term)

            if partners:
                for partner in partners:
                    term_and_partner_pmids = get_pmcids_for_term_and_partner(term, partner, retmax=retmax)
                    if len(term_and_partner_pmids) > 0:
                        pmids.extend(term_and_partner_pmids)
                        partner_dict[partner] = term_and_partner_pmids
                        logger.info(f"Found {len(term_and_partner_pmids)} PMIDs for gene {term} and {partner}")
                        logger.info(f'{term}\t{partner}\t{", ".join(term_and_partner_pmids)}')
                    else:
                        logger.info(f"No PMIDs found for {term} and {partner}")
            else:
                logger.info(f"No partners found for {term}")

        # Get PMIDs for the term
        else:
            pmids = get_pmcids(term, retmax=retmax)
            logger.info(f"Found {len(pmids)} PMIDs for gene {term}")

        
        # Part 2: Download the PDFs
        if len(pmids) == 0:
            logger.info(f"No PMIDs found for gene '{term}'")
            continue
        else:
            for pmid in pmids:
                get_pdf(pmid)


        # Part 3: Determine the relevancy of the PDFs
        # question = f"What is the role of the gene {term}?"
        # question = f"What is the role of the gene {partner}?"
        # question3 = f"What, if any, physical interactions occur between {term} and {matching_partner}"
        
        # still in for term in terms loop
        for pmid in pmids:
            logger.info("\n")
            results.append(process_pdf_relevancy(pmid, term, get_partners, template, no_delete, partner_dict))
            
            
        for partner, pmid_list in partner_dict.items():
            if pmid in pmid_list:
                print(f'{term}\t{partner}\t{pmid_list}')
            
    for result in results:
        print(result)

if __name__ == "__main__":
    main()

from litscan import get_string_interaction_partners
from litscan import get_pmcids
from litscan import get_pmcids_for_term_and_partner
from litscan import get_pdf
from litscan import is_pdf_relevant

import os
from time import sleep
from typing import List


import argparse

# Initialize the parser
parser = argparse.ArgumentParser(description="A simple download and relevancy testing program.")

# Add arguments TODO: This needs to be tested.
parser.add_argument("--template", type=str, help="The question you want to ask.",
        default="What is the role of the gene {}?")
parser.add_argument("--terms", nargs="+", help="List of items", 
        default=["WHSC1", "RTCB", "WRN", "P2X7", "NLRP3", "CSF1R", "ALKBH1", "NMNAT2", "NSUN2", "RTCB"])
parser.add_argument("--retmax", type=int, default=20, help="The maximum number of papers to download.")
parser.add_argument("--no_delete", action="store_true", help="If set, do not delete pdf if not relevant")
parser.add_argument("--get_partners", action="store_true", default=False, help="Use partner data")


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

# For testing
get_partners = True

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
        print(f"chat response {chat_response} does not contain choices")
        return 0
    
    answer = chat_response.choices[0].message.content
    print(f'Is {pmid}.pdf relevant to the question: {question}')
    print(f'Answer: {answer}')
    
    is_relevant = not answer.lower().startswith('no')
    if not is_relevant and delete_if_no:
        print(f'removing {pmid}.pdf')
        os.remove(f'{pmid}.pdf')
    
    return 1 if is_relevant else -1


def get_relevant_partners(term: str) -> List[str]:
    """Get relevant interaction partners for a given term above a score threshold."""
    partners = []
    partner_data = get_string_interaction_partners(term, limit=Config.PARTNER_LIMIT)
    
    for i, item in enumerate(partner_data):
        partner = item["preferredName_B"]
        print(f'{i}\t{item["preferredName_A"]}\t{item["preferredName_B"]}\t{item["score"]}')
        
        if item["score"] > Config.PARTNER_SCORE_THRESHOLD:
            partners.append(partner)
    
    return partners

def main():

    for term in terms:
        pmids = [] 
        partner_dict = {}

        # Part 1: Get pmids for term AND each partner
        if get_partners == True:
            partners = get_relevant_partners(term)

            if partners:
                for partner in partners:
                    term_and_partner_pmids = get_pmcids_for_term_and_partner(term, partner, retmax=retmax)
                    if term_and_partner_pmids:
                        pmids.extend(term_and_partner_pmids)
                        partner_dict[partner] = term_and_partner_pmids
                        print(f"Found {len(term_and_partner_pmids)} PMIDs for gene {term} and {partner}")
                    else:
                        print(f"No PMIDs found for {term} and {partner}")
            else:
                print(f"No partners found for {term}")

        # Get PMIDs for the term
        else:
            pmids = get_pmcids(term, retmax=retmax)
            print(f"Found {len(pmids)} PMIDs for gene {term}") #: {pmids}")

        
        # Part 2: Download the PDFs
        if len(pmids) == 0:
            print(f"No PMIDs found for gene '{term}'")
            continue
        else:
            for pmid in pmids:
                get_pdf(pmid)


        # Part 3: Determine the relevancy of the PDFs
        # question = f"What is the role of the gene {term}?"
        # question = f"What is the role of the gene {partner}?"
        for pmid in pmids:
            print("\n")

            if os.path.exists(f'{pmid}.pdf') == False:
                print(f'file {pmid}.pdf does not exist')
                continue  # Skip to the next pmid if the PDF does not exist
            
            if get_partners == False:
                question = template.format(term)
                process_relevancy_check(pmid, question, delete_if_no=not no_delete) # delete if no_delete is False

            else:
                # Find which partner's PMIDs contain this pmid
                matching_partner = None
                for p, pmid_list in partner_dict.items():
                    if pmid in pmid_list:
                        matching_partner = p
                        score = 0

                        question1 = template.format(term)
                        score += process_relevancy_check(pmid, question1)

                        question2 = template.format(matching_partner)
                        score += process_relevancy_check(pmid, question2)

                        print(f'score {score}')
                        if (score == -2) and (not no_delete):
                            print(f'removing {pmid}.pdf')
                            os.remove(f'{pmid}.pdf')

                        if score == 2:
                            question3 = f"What, if any, physical interactions occur between {term} and {matching_partner}"
                            score += process_relevancy_check(pmid, question3)

                        if score != 3 and not no_delete:
                            print(f'removing {pmid}.pdf')
                            os.remove(f'{pmid}.pdf')

if __name__ == "__main__":
    main()

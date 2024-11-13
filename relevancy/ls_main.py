import os
from pprint import pprint
from time import sleep
from litscan import get_pmcids, get_pdf, is_pdf_relevant

# terms = ["WHSC1", "RTCB", "WRN", "P2X7", "NLRP3", "CSF1R", "ALKBH1", "NMNAT2", "NSUN2", "RTCB"]

import argparse

# Initialize the parser
parser = argparse.ArgumentParser(description="A simple download and relevancy testing program.")

# Add arguments TODO: This needs to be tested.
parser.add_argument("--template", type=str, help="The question you want to ask.",
        default="What is the role of the gene {}?")
parser.add_argument("--terms", nargs="+", help="List of items", 
        default=["WHSC1", "RTCB", "WRN", "P2X7", "NLRP3", "CSF1R", "ALKBH1", "NMNAT2", "NSUN2", "RTCB"])
parser.add_argument("--retmax", type=int, default=20, help="The maximum number of papers to download.")
parser.add_argument("--no-delete", action="store_false", help="Delete pdf if not relevant")

# Parse arguments
args     = parser.parse_args()
retmax   = args.retmax
template = args.template
terms    = args.terms
no_delete   = args.no_delete

def main():

    for term in terms:
        #question = f"What is the role of the gene {term}?"
        question = template.format(term)
        pmids = get_pmcids(term, retmax=retmax)
        print(f"Found {len(pmids)} PMIDs for gene {term}") #: {pmids}")

        if len(pmids) == 0:
            print(f"No PMIDs found for gene '{term}'")
    
        for pmid in pmids:
            print("\n")

            get_pdf(pmid)
            if os.path.exists(f'{pmid}.pdf') == False:
                continue  # Skip to the next pmid if the PDF does not exist
            
            chat_response = is_pdf_relevant(f"{pmid}.pdf", question)
            if chat_response is None:
                print (f"chat response {chat_response} does not contain choices")
            else:
                answer = chat_response.choices[0].message.content

                print(f'Is the paper relevant to the question: {question}')
                print(f'Answer: {answer}')

                if answer.lower().startswith('no') and no_delete == False:
                    os.remove(f'{pmid}.pdf')

                sleep(10)


if __name__ == "__main__":
    main()


from litscan import get_string_interaction_partners
from litscan import is_pdf_relevant
from litscan import get_pdf
from litscan import get_pmcids

import os
from time import sleep



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
parser.add_argument("--get_partners", action="store_true", default=False, help="Use partner data")

# Parse arguments
args     = parser.parse_args()
retmax   = args.retmax
template = args.template
terms    = args.terms
no_delete   = args.no_delete
get_partners = args.get_partners

# For testing
get_partners = True
terms = ["WRN"]

def main():


    for term in terms:
        pmids = [] 
        partner_dict = {}

        # Get pmids for term AND each partner
        if get_partners == True:
            partners=[]
            partner_data = get_string_interaction_partners(term, limit=10)
            for i, item in enumerate(partner_data):
                partner = item["preferredName_B"]
                print(f'{i}\t{item["preferredName_A"]}\t{item["preferredName_B"]}\t{item["score"]}')
                partners.append(partner)

            # Get PMIDs for term AND partners
            if partners:
                for partner in partners:

                    # construct the search term
                    term_and_partner = f'{term}+AND+{partner}'
                    # get the PMIDs
                    term_and_partner_pmids = get_pmcids(term_and_partner, retmax=retmax)
                    # add the PMIDs to the list
                    if term_and_partner_pmids:
                        pmids.extend(term_and_partner_pmids)
                    # associate the PMIDs with the partner
                    partner_dict[partner] = term_and_partner_pmids

                    print(f"Found {len(term_and_partner_pmids)} PMIDs for gene {term_and_partner}")
                    print(f"Total PMIDs: {len(pmids)}")

                else:
                    print(f"No PMIDs found for {term_and_partner}")
            else:
                print(f"No partners found for {term}")

        # Get PMIDs for the term
        else:
            pmids = get_pmcids(term, retmax=retmax)
            print(f"Found {len(pmids)} PMIDs for gene {term}") #: {pmids}")

        # Download the PDFs
        if len(pmids) == 0:
            print(f"No PMIDs found for gene '{term}'")
            continue
        else:
            for pmid in pmids:
                get_pdf(pmid)

        # Determine the relevancy 
        # question = f"What is the role of the gene {term}?"
        # question = f"What is the role of the gene {partner}?"
        for pmid in pmids:
            print("\n")

            # get the PDF
            get_pdf(pmid)
            if os.path.exists(f'{pmid}.pdf') == False:
                print(f'file {pmid}.pdf does not exist')
                # continue  # Skip to the next pmid if the PDF does not exist
            
            if get_partners == False:
                question = template.format(term)
                chat_response = is_pdf_relevant(f"{pmid}.pdf", question)
                if chat_response is None:
                    print (f"chat response {chat_response} does not contain choices")
                else:
                    answer = chat_response.choices[0].message.content
                    print(f'Is the paper relevant to the question: {question}')
                    print(f'Answer: {answer}')
                    if answer.lower().startswith('no') and no_delete == False:
                        os.remove(f'{pmid}.pdf')
            else:
                # Find which partner's PMIDs contain this pmid
                matching_partner = None
                for p, pmid_list in partner_dict.items():
                    if pmid in pmid_list:
                        matching_partner = p
                        question = template.format(matching_partner)
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

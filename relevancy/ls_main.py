import os
from time import sleep
from litscan import get_pmcids, find_similar_papers, get_pdf, is_pdf_relevant

gene_symbols = ["RTCB", "WRN", "P2X7", "NLRP3", "CSF1R", "ALKBH1", "NMNAT2", "NSUN2", "WHSC1"]

def main():

    for gene_symbol in gene_symbols:
        question = f"What is the role of the gene {gene_symbol}?"
        pmids = get_pmcids(gene_symbol)
        print(f"Found {len(pmids)} PMIDs for gene {gene_symbol}") #: {pmids}")

        if len(pmids) == 0:
            print(f"No PMIDs found for gene '{gene_symbols[1]}'")
    
        for pmid in pmids:
            get_pdf(pmid)

            chat_response = is_pdf_relevant(f"{pmid}.pdf", question)
            answer = chat_response.choices[0].message.content

            print(f'Is the paper relevant to the question: {question}')
            print(f'answer: {answer}')

            sleep(10)

            if chat_response.choices[0].message.content.lower().startswith('yes'):
                print(f'getting similar papers for {pmid}')
                similar_pmids = find_similar_papers(pmids)
                if len(similar_pmids) == 0:
                    print(f"No similar papers found for gene '{gene_symbols[1]}'")
                else:
                    print(f"Found {len(similar_pmids)} similar papers PMIDs for gene '{gene_symbols[1]}'") #: {similar_pmids}")
                    for similar_pmid in similar_pmids:
                        get_pdf(similar_pmid)
                        chat_response = is_pdf_relevant(f"{similar_pmid}.pdf", question)
                        print(f'Is the paper relevant to the question: {question}')
                        print(f'answer: {answer}')
            
                        if chat_response.choices[0].message.content.lower().startswith('yes'):
                            print(f'{similar_pid} will be saved.')
                        else:
                            print(f'{similar_pmid}.pdf is being deleted')
                            os.remove(f'{similar_pmid}.pdf')
                            print(f'{similar_pmid}.pdf has been deleted.')

                        sleep(10)
                    
            else:
                print(f'{pmid}.pdf is being deleted')
                os.remove(f'{pmid}.pdf')
                print(f"{pmid}.pdf has been deleted.")


if __name__ == "__main__":
    main()

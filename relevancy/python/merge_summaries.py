import sys
sys.path.append("..")

import os
import argparse

from Configs import LLMConfig
from relevancy.PDFSummarizer import PDFSummarizer
from ast import literal_eval

def read_scores_file(file_path):
    """Read a file containing tuples of the form (term, partner, pmid, score) 
    and return a list of tuples e.g. ('RTCB', 'RTCA', '6222203', 1)"""

    tuples = []
    with open(file_path, 'r') as file:
        for line in file:
            if line.strip():  # Skip empty lines
                # Parse the line as a Python literal
                tuple_data = literal_eval(line.strip())
                tuples.append(tuple_data)
    return tuples

def main():
    parser = argparse.ArgumentParser(description='Process scores file and generate summaries')
    parser.add_argument('scores_file', help='Path to the scores file', default='RUN001/RTCB/scores.test')
    args = parser.parse_args()

    config = LLMConfig()
    summarizer = PDFSummarizer(config)
    summaries = []
        
    scores = read_scores_file(args.scores_file)
    scores = [score for score in scores if score[3] == 3]

    for score in scores:
        print(f"Processing {score}")

        term, partner, pmid, score = score
        pdf_path = f"RUN001/{pmid}.pdf"
        if os.path.exists(pdf_path):
            summarizer.extract_text(pdf_path)
            interaction_summary = summarizer.ask_question(f"What is the interaction between {term} and {partner}?")
            summary = summarizer.summarize()
            print(interaction_summary)
            summaries.append(interaction_summary)
    

    # pass all the summaries to the summarizer with the question
    summarizer.context = "\n\n".join(summaries)
    question = "What are the main findings? If there are findings that disagree, please mention them."
    final_summary = summarizer.ask_question(question)
    print(f"Final summary: {final_summary}")


    # Write summaries to file
    with open("RUN001/RTCB/summaries.txt", "w") as file:
        for summary in summaries:
            file.write(summary + "\n")


    #print(f"conversation history: {summarizer.conversation_history}")
    

if __name__ == "__main__":
    main()

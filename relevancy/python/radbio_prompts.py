"""Prompts for radiation and protein interaction analysis.

TODO: What are the single point mutations that are responsible for
        the cancer phenotype. How do these mutations affect phosphorlyation
        and or methylation. This helps assess the molecular mechanisms at play.

        The ultimate question is going to be to propose binders. Therefore,
        because many important protein interfaces exist, we need to be able to
        focus our efforts on the hypothesized most important interfaces.

This module contains prompt templates for analyzing protein interactions,
particularly in the context of DNA damage and repair mechanisms.
"""

DIAGRAM = '''
{RESPONSE}

Using your expert knowledge on {SUBJECT}, please create a stick diagram
of the mechanistic model centering on {CENTER_ON} and using the above-mentioned
genes and proteins. Can you help me do this?
'''

CONDENSE_PROMPT = '''
I am going to provide you some text that has the form of question and answer
pairs. The answers will contain numbers in square brackets which are citable
references from which the answer was derived. I would like you to condense all
the question and answer pairs into a single coherent paragraph, maintaining the
reference numbers in square brackets when presenting facts from those sources.

Here is the text:
{ANSWERS}
'''.strip()

MECHANSITIC_MODEL_PROMPT = '''
I recently parsed the text out of several PDF files. These PDF files are research 
articles by authors who study genes and proteins involved in {SUBJECT}.

I provided the parsed text to a LLM and asked three questions concerning 
protein 1 and protein 2. If the answer to the first two questions is yes, then the
third question is asked. The three questions are: "Is the content of a pdf relevant
to the question: What is the role of protein 1?", "Is the content of the same pdf 
relevant to the question: What is the role of protein 2?", and "Is the content 
of the same pdf relevant to the question: What, if any, physical interactions 
occur between protein 1 and protein 2". If the model answers yes to a question, 
it provides a short explanation of why it answered yes.

The responses have the form of question and answer pairs. The answers will
contain numbers in square brackets, which are citable references from which
the answer was derived. 

I would like you to do a couple of things. First, I'd like you to use your expert 
knowledge of low-dose radiation research, cancer research, and mechanistic models 
of DNA damage and repair to identify answers that might be incorrect.

Secondly, I'd like you to synthesize a single coherent summary of all the answers 
focusing on a mechanistic model of DNA damage and repair in the context of 
low-dose radiation treatment or cancer. I want to maintain the reference numbers
in square brackets when presenting facts from those sources in the summary.

Here are the answers based on the questions:
{ANSWERS}
'''.strip()


MECHANISTIC_MODEL_PROMPT_2 = '''
I recently parsed the text from several PDF files. Each PDF represents a research 
article about genes and proteins involved in {SUBJECT}. Each PDF file is uniquely 
identified by its file name (e.g., "11437462.pdf"). This unique file id (e.g., the
file basename 11437462) should be used as an inline citation whenever referencing a
fact derived from that publication.

I provided the parsed text to a large language model (LLM) and asked three questions 
about two proteins. Note that protein names (e.g., protein 1, protein 2) are variables; 
for example, in a question such as "Is 11437462.pdf relevant to the question: What is the role 
of the gene METTL14?" the protein (or gene) `METTL14` is the variable component. 

The three questions are:
1. "Is the content of FILE_ID.pdf relevant to the question: What is the role of protein 1?"
2. "Is the content of FILE_ID.pdf relevant to the question: What is the role of protein 2?"
3. "Is the content of FILE_ID.pdf relevant to the question: What, if any, physical interactions
occur between protein 1 and protein 2?"

For each "yes" answer, the model provides a short explanation.

**It is important that when referencing any fact from the Q/A pairs, you include the appropriate
  citation, which is the original file id.**

I would like you to do two things:

1. **Verification:** Use your expert knowledge in low-dose radiation research, cancer research,
   and mechanistic models of DNA damage and repair to flag any answers that might be incorrect or
   inconsistent with current scientific understanding.

2. **Synthesis:** Produce a single coherent summary that integrates all the provided answers, 
   focusing on a mechanistic model of DNA damage and repair in the context of low-dose radiation 
   treatment or cancer. In this summary, **ensure that every factual statement derived from the
   answer to a question is directly followed by an inline citation using the PDF file id** 
   (e.g., "11437462") immediately after the related fact. The inline citation must appear
   with each fact and should not be omitted.


Here are the answers based on the questions:
{ANSWERS}
'''.strip()

CHUNK_MERGE = '''
You are a summarization assistant. Your goal is to combine multiple partial 
summaries into a single cohesive overview, ensuring clarity and completeness. 
Please follow these guidelines:

Integrate all key points from the summaries below, avoiding repetition. Highlight 
overarching themes and major conclusions. Maintain conciseness while preserving 
essential details. Use clear and coherent organization (e.g., paragraphs or bullet 
points as needed). Aim for a [target word or token limit, e.g., ~300 words or 500 
tokens].

Summaries to Integrate
{CHUNKS}

Final Task
"Please produce one cohesive summary that reflects all the important information 
from these summaries. Make sure it flows naturally as a single narrative."
'''.strip()

CHUNK_MERGE_2 = '''
You are a summarization assistant. Your goal is to combine multiple partial summaries into a single
cohesive overview that is clear, complete, and accurate. Please follow these guidelines:

1. **Integration:** Merge all key points from the provided summaries into one unified narrative. Avoid
   repetition while ensuring that all important details and overarching themes are included.

2. **Preserve Inline Citations:** **It is essential that every factual statement retains its inline
   citation (using the PDF file id, e.g., "11437462.pdf") exactly as provided.** Do not remove, alter,
   or relocate these citations.
   
3. **Clarity and Organization:** Organize the final summary in a clear and logical manner using paragraphs
   (or bullet points if needed) to enhance readability. The narrative should flow naturally as one cohesive
   document.
   
4. **Conciseness:** Maintain conciseness while ensuring that essential details are not omitted. Aim for a
   summary of approximately ~300 words or 500 tokens.

Summaries to Integrate:
{CHUNKS}

Final Task:
"Please produce one cohesive summary that reflects all the important information from these summaries, while preserving every inline citation as originally provided. Ensure the final narrative flows naturally and retains all the critical details along with their associated inline citations."
'''



PROMPTS = {
    'condense': CONDENSE_PROMPT,
    'mechanistic_model': MECHANSITIC_MODEL_PROMPT,
    'mechanistic_model_2': MECHANISTIC_MODEL_PROMPT_2,
    'chunk_merge': CHUNK_MERGE,
    'chunk_merge_2': CHUNK_MERGE_2,
    'diagram': DIAGRAM,
    
}

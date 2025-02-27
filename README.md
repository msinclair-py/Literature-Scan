# LiteratureScan
LLM and Agentic workflows for scraping, reading and processing scientific literature.
Utilizes OpenAI API for model hosting and requires an API key to be stored in the
environment variable, OPENAI_API_KEY. Recommended model is currently gpt-4o-mini due
to both the efficiency, accuracy and low cost. gpt-4o is also good but costs around 10x
as much per token (a paper is usually ~15k tokens).

## Installation
I have provided an environment.yaml file for constructing a conda environment. If 
this does not work the primary requirements are all found in the requirements.txt
file.

Minimal installation:
- openai
- tiktoken
- requests
- PyPDF2

Agentic workflows (WIP) will require langchain as well.

## Running literature scan
An example of a PMC scraping workflow is in `examples/download_papers.py`. In short,
you need to provide some search term to query PMC, a maximum number of papers to
download and a set of questions, and optional weights, to score how well a paper matches
your needs.

To enter an interactive summarization loop you can run `relevancy/PDFSummarizer.py`
for a local paper like so:
```python PDFSummarizer.py /path/to/paper.pdf```
After first summarizing the paper, you will enter a while loop where you can continue
to ask the model questions until you enter 'quit'.

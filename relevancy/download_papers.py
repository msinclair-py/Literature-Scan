from configs import LLMConfig, LitScanConfig
from datetime import datetime
from litscan import Logger, PMCScanner
import os
import pickle

api_key = os.environ.get('OPENAI_API_KEY')
term = 'lolcde'
outdir = 'test_papers'
pmcids = None # make into a list to pass local papers into this workflow
questions = [
    #f'Does this paper discuss the {term} protein?',
    f'Does this paper discuss specific residues of {term} by residue ID?',
    f'Does this paper discuss biologically relevant binding interfaces of {term}?',
    f'Does this paper discuss one or more point mutants of {term} related to dysfunction?',
    f'Does this paper discuss intrinsically disordered proteins or regions?'
]
weights = [3, 1, 2, 1]

llmconfig = LLMConfig(
    api_key=api_key,
    base_url=None, # let OpenAI client route this
    model='gpt-4o-mini',
    temperature=0.0, # be more deterministic
    logfile='testing.log'
)

lsconfig = LitScanConfig(
    retmax=100,
    openai_api_key=api_key,
    openai_base_url=None,
    openai_model='gpt-4o-mini'
)

os.makedirs(outdir, exist_ok=True)
logger = Logger(config=llmconfig)
scraper = PMCScanner(logger=logger, cfg=lsconfig, outdir=outdir)
pmcids = scraper.get_ids(term)
results = {}
for pmcid in pmcids:
    scraper.get_pdf(pmcid)
    print(f'Is {pmcid} relevant?')
    responses = []
    score = 0

    results[pmcid] = scraper.is_pdf_relevant(f'{pmcid}.pdf', 
                                             questions, 
                                             weights)

timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
with open(f'{outdir}/responses_{timestamp}.pkl', 'wb') as f:
    pickle.dump(results, f)

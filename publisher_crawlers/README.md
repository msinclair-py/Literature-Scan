# Web Crawling for various platforms
Each publisher/platform has its own MVP. The websites structure various quite a bit so it was initially easier to sperate implementaitons. Tis is likely not optimal at this point and could be re-structured with an abstract base class.


## Spider/Meta Crawler
Each module seeks out URLs before scraping papers individually.Spider/Meta crawlers serve this function. For example, `BioRXiV_Meta_Creator` is a class that searches BioRXiVs meta database (by date, not keyword!) and stores meta information like DOI, author names, paper title, abstract, etc. into a local CSV file. See `./registry`. Since I assume time is of the essence (it was for me), it supports parallel querying in bulk through an integer index.
An agentic crawler may want to have this database available already (and previously ran a cos similiarity search over abstracts given some prompt, classified a document's content as interesting based on the abstract text alone). In turn, bulk meta crawling may be desirable even in this context - also to stay up to date on publications that are not yet in our PRD etc. datasets.

It runs through `run_meta_creator.py`, e.g.
```
meta = BioRXiV_Meta_Creator()
meta.store_biorxiv_meta(i=args.i)
``` 

## Crawler
Given a page URL, the crawler scrapes 3 items
- PDF (via download)
- HTML full text version of the paper (usually synthesized on the website from text source file)
- additional meta data (extent varies drastically from platform to platform)
All items are useful. Meta data may not be available for some platforms through the spider, so looking up keywords etc. in the fulltext URL comes in handy. 
The HTML text is extremely useful as it circumvents PDF parsing altogether. I believe this attribute is underappreciated given the time and (lack of accuracy) of most of our parsers.
The PDF file may be the required input to various pipelines so scraping it is reasonable. 

The `run_X_scraper.py` trigger the research paper crawlers, e.g.

```
bio_arx = BioArXiV_MVP(i_start=i_start)

# download content
bio_arx.get_arxiv_articles_with_html()
``` 

## Lessons from scraping
- journals are stingy: sleep times are required to be 7-15 seconds
- APIs are tricky (in particular arxiv) as it seems to slow you dne without letting you know
- `robots.txt` is not a suggestion: they tend to block or - even worse - drastically slow down (quickly); run it from your home IP rather than ANL if possible
- bulk scraping remains a necessity (even for agents) to stay "up to date" and be able to merge paper content onto semantic scholar reference graphs
- pull the entire HTML (for full text or meta information); do not scrape on-the-fly as many articles have slightly different layout; this allows experimentation on the local `.html` file rather than repeateldy requesting it from the publisher (we have enough disk space)

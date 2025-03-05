from configs import LLMConfig
from openai import OpenAI
from pathlib import Path
import pymupdf
import tiktoken
from typing import List, Union

PathLike = Union[str, Path]
FileLike = Union[str, Path, List[str]]

class PDFSummarizer:
    """
    PDFSummarizer provides functionality to extract, summarize and analyze PDF 
    documents using LLMs.
    
    The class handles:
    - PDF text extraction
    - Text chunking to fit within LLM context windows 
    - Document summarization
    - Interactive Q&A about the document content
    - Conversation history tracking
    
    Example usage:
        config = LLMConfig()
        summarizer = PDFSummarizer(config)
        
        # Extract and summarize PDF
        summarizer.extract_text("paper.pdf")
        summary = summarizer.summarize()
        
        # Ask questions
        answer = summarizer.ask_question("What are the main findings?")
    """
    def __init__(self, config: LLMConfig):
        self.config = config
        self.client = OpenAI(
            api_key=config.api_key,
            base_url=config.base_url
        )
        self.context = ""
        self.conversation_history = []
        self.tokenizer = tiktoken.encoding_for_model("gpt-4o-mini")
        self.max_chunk_tokens = 15000  # Adjust this based on your model's limits
        self.overlap_tokens = 5000     # Overlap between chunks to maintain context

    def extract_text(self, pdf_path: str, save_text: bool = True) -> str:
        """Extract text content from PDF file and assign to context."""
        context = ''
        doc = pymupdf.open(pdf_path)
        txt_path = pdf_path.rsplit('.', 1)[0] + '.txt'
        out = open(txt_path, 'wb') if save_text else None
        for page in doc:
            text = page.get_text().encode('utf8')
            context += text

            if save_text:
                out.write(text)
                out.write(bytes((12,)))

        self.context = context
        
        if save_text:
            out.close()

        return context

    def _chunk_text(self, text: str) -> list[str]:
        """Split text into overlapping chunks based on token count"""
        chunks = []
        tokens = self.tokenizer.encode(text)

        start = 0
        while start < len(tokens):
            # Get chunk of tokens
            end = start + self.max_chunk_tokens
            chunk_tokens = tokens[start:end]

            # Convert chunk tokens back to text
            chunk_text = self.tokenizer.decode(chunk_tokens)
            chunks.append(chunk_text)

            # Move start position, accounting for overlap
            start = end - self.overlap_tokens

        return chunks

    def summarize(self) -> str:
        """Generate summary of PDF content using chunks"""
        chunks = self._chunk_text(self.context)
        chunk_summaries = []

        # Summarize each chunk
        for i, chunk in enumerate(chunks):
            prompt = f"Please summarize part {i+1} of {len(chunks)} of the text:\n\n{chunk}"
            summary = self._get_completion(prompt)
            chunk_summaries.append(summary)

        # Combine chunk summaries
        combined_summary = "\n\n".join(chunk_summaries)
        if len(chunks) > 1:
            # Create final summary of summaries
            final_prompt = f"Please provide a coherent summary combining these section summaries:\n\n{combined_summary}"
            final_summary = self._get_completion(final_prompt)
        else:
            final_summary = combined_summary

        # Update conversation history
        self.conversation_history.append({
            "role": "user",
            "content": "Generate summary"
        })
        self.conversation_history.append({
            "role": "assistant",
            "content": final_summary
        })

        return final_summary

    def ask_question(self, question: str) -> str:
        """Ask follow-up question about the PDF content using chunks"""
        chunks = self._chunk_text(self.context)
        chunk_responses = []

        # Get response from each chunk
        for chunk in chunks:
            prompt = f"Given the following text:\n\n{chunk}\n\nPlease answer this question: {question}"
            response = self._get_completion(prompt)
            chunk_responses.append(response)

        # Combine responses if multiple chunks
        if len(chunks) > 1:
            combined_responses = "\n\n".join(chunk_responses)
            final_prompt = f"Please provide a coherent answer combining these responses to the question '{question}':\n\n{combined_responses}"
            final_response = self._get_completion(final_prompt)
        else:
            final_response = chunk_responses[0]

        # Update conversation history
        self.conversation_history.append({
            "role": "user",
            "content": question
        })
        self.conversation_history.append({
            "role": "assistant",
            "content": final_response
        })

        return final_response

    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in a text string"""
        return len(self.tokenizer.encode(text))

    def _get_completion(self, prompt: str) -> str:
        """Helper method to get LLM completion"""
        try:
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=[{"role": "user", "content": prompt}],
                # max_tokens=self.config.max_tokens,
                temperature=self.config.temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error getting LLM response: {str(e)}"

    def save_conversation(self, output_path: str = None, term: str = None) -> str:
        """Save conversation history to a file"""
        if output_path is None:
            # Generate default filename using timestamp
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if term is None:
                output_path = f"conversation_{timestamp}.txt"
            else:
                output_path = f"conversation_{timestamp}_{term}.txt"

        with open(output_path, 'w', encoding='utf-8') as f:
            for message in self.conversation_history:
                role = message["role"].capitalize()
                content = message["content"]
                f.write(f"\n{role}:\n{content}\n")
                f.write("-" * 50 + "\n")

        return output_path

class BulkPDFExtractor:
    """
    For processing multiple PDF files at once for text extraction.
    """
    def __init__(self, directory: PathLike, files: FileLike,
                 output_directory: PathLike):
        self.directory = directory
        self.output_directory = output_directory

        if isinstance(files, list):
            _files = files
        else:
            _files = [line.strip() for line in open(files).readlines()]

        self.files = set(files)

    def process_pdfs(self) -> None:
        for pdf_file in self.directory.glob('*.pdf'):
            name = pdb_file.name.strip('.pdf')

            if name in self.files:
                print('Processing: {pdf_file}')
                text = extract_pdf_text(pdf_file) # this currently comes from litscan.py
                output_file = self.output_dir / name + '.txt'

                with open(str(output_file, 'w')) as f:
                    f.write(text)

if __name__ == '__main__':
    import os
    import sys
    if len(sys.argv) < 2:
        raise RuntimeError('Usage: python PDFSummarizer.py <pdf_file> <*args:terms>')

    config = LLMConfig()
    summarizer = PDFSummarizer(config)

    pdf = sys.argv[1]
    if len(sys.argv) > 2:
        term = sys.argv[2]
    else:
        term = None

    summarizer.extract_text(pdf)
    print('\nInitial Summary:')
    print(summarizer.summarize())

    # Interactive question loop
    print('\nEnter questions about the document (or "quit" to exit):')
    while True:
        question = input('\nQuestion: ').strip()
        if question.lower() == 'quit':
            break
        print('\nAnswer:')
        print(summarizer.ask_question(question))

    # save conversation when exiting
    output_file = summarizer.save_conversation()
    print(f'\nConversation saved to: {output_file}')

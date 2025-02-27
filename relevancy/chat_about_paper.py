from config import LLMConfig
from pathlib import Path
from PDFSummarizer import PDFSummarizer

class JournalClub:
    def __init__(self, pdf_file: PathLike,
                 config: LLMConfig,
                 summarizer: PDFSummarizer):
        self.pdf_file = pdf_file
        self.config = config
        self.summarizer = summarizer

    def preprocess(self):
        _ = self.summarizer.extract_text(self.pdf_file, save_text=False)

    def ask_questions(self):
        print('\nInitial Summary:')
        print(self.summarizer.summarize())

        print('\nEnter questions about the document (or "quit" to exit):')
        while True:
            question = input('\nQuestion: ').strip()
            if question.lower() == 'quit':
                break
            print('\nAnswer:')
            print(self.summarizer.ask_question(question))
        
        output_file = summarizer.save_conversation()
        print(f'\nConversation saved to: {output_file}')

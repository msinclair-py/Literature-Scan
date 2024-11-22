import sys
from openai import OpenAI
import PyPDF2
import tiktoken

class LLMConfig:
    """Configuration settings for LLM interactions"""
    def __init__(self):
        self.api_key = "cmsc-35360"
        self.base_url = "http://localhost:9999/v1"
        self.model = "llama31-405b-fp8"
        # self.max_tokens = 36000
        self.temperature = 0.7

class PDFSummarizer:
    def __init__(self, config: LLMConfig):
        self.config = config
        self.client = OpenAI(
            api_key=config.api_key,
            base_url=config.base_url
        )
        self.context = ""
        self.conversation_history = []
        self.tokenizer = tiktoken.encoding_for_model("gpt-3.5-turbo")
    
    def extract_text(self, pdf_path):
        """Extract text content from PDF file"""
        text = ""
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text()
        self.context = text
        return text

    def summarize(self):
        """Generate initial summary of PDF content"""
        prompt = f"Please provide a comprehensive summary of the following text:\n\n{self.context}"
        response = self._get_completion(prompt)
        self.conversation_history.append({
            "role": "user",
            "content": "Generate summary"
        })
        self.conversation_history.append({
            "role": "assistant",
            "content": response
        })
        return response

    def ask_question(self, question):
        """Ask follow-up question about the PDF content"""
        prompt = f"Given the following text:\n\n{self.context}\n\nPlease answer this question: {question}"
        response = self._get_completion(prompt)
        self.conversation_history.append({
            "role": "user",
            "content": question
        })
        self.conversation_history.append({
            "role": "assistant",
            "content": response
        })
        return response

    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in a text string"""
        return len(self.tokenizer.encode(text))
    
    def _get_completion(self, prompt):
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

    def save_conversation(self, output_path=None):
        """Save conversation history to a file"""
        if output_path is None:
            # Generate default filename using timestamp
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"conversation_{timestamp}.txt"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for message in self.conversation_history:
                role = message["role"].capitalize()
                content = message["content"]
                f.write(f"\n{role}:\n{content}\n")
                f.write("-" * 50 + "\n")
        
        return output_path

def main():
    if len(sys.argv) != 2:
        print("Usage: python script.py <pdf_file>")
        sys.exit(1)

    config = LLMConfig()
    summarizer = PDFSummarizer(config)
    
    # Extract and summarize PDF
    pdf_path = sys.argv[1]
    summarizer.extract_text(pdf_path)
    print("\nInitial Summary:")
    print(summarizer.summarize())
    
    # Interactive question loop
    print("\nEnter questions about the document (or 'quit' to exit):")
    while True:
        question = input("\nQuestion: ").strip()
        if question.lower() == 'quit':
            break
        print("\nAnswer:")
        print(summarizer.ask_question(question))
    
    # Save conversation when exiting
    output_file = summarizer.save_conversation()
    print(f"\nConversation saved to: {output_file}")

if __name__ == "__main__":
    main()

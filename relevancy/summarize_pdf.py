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
        self.max_chunk_tokens = 4000  # Adjust this based on your model's limits
        self.overlap_tokens = 200     # Overlap between chunks to maintain context
    
    def extract_text(self, pdf_path):
        """Extract text content from PDF file"""
        text = ""
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text()
        self.context = text
        return text

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

    def summarize(self):
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

    def ask_question(self, question):
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

    def save_conversation(self, output_path=None, term=None):
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

def main():
    if len(sys.argv) != 2:
        print("Usage: python script.py <pdf_file>")
        sys.exit(1)

    config = LLMConfig()
    summarizer = PDFSummarizer(config)
    
    # Extract and summarize PDF
    pdf_path = sys.argv[1]
    if sys.argv[2]:
        term = sys.argv[2]
    else:
        term = None
    
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

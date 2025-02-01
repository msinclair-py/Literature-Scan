
# A simple command to extract text
from litscan import extract_pdf_text

import argparse

def get_pdf_filenames_from_file(file_path):
    """
    Reads a list of PDF filenames from an input file.
    
    Args:
        file_path (str): Path to the input file containing PDF filenames.

    Returns:
        set: A set of PDF filenames (without directory path).
    """
    with open(file_path, "r") as file:
        return {line.strip() for line in file}

def process_pdfs(directory, input_file):
    """
    Processes only the PDFs listed in the input file that exist in the directory.

    Args:
        directory (str): Path to the directory containing PDFs.
        input_file (str): Path to the file containing a list of PDF filenames.
    """
    directory = Path(directory)
    
    # Read the list of valid PDF filenames from input file
    pdf_filenames = get_pdf_filenames_from_file(input_file)

    for pdf_file in directory.glob("*.pdf"):  # Get only .pdf files in the directory
        if pdf_file.name.strip(".pdf") in pdf_filenames:  # Process only if it's in the input file
            print(f"Processing: {pdf_file}")  # Replace with actual processing logic
            text=extract_pdf_text(pdf_file)

            output_file = os.path.join(output_dir, pdf_file.name.strip(".pdf") + ".txt")
            with open(output_file, "w") as file:  # 'w' mode overwrites the file if it exists
                file.write(text)

def main():
    # Create argument parser
    parser = argparse.ArgumentParser(description="Process an input file and save to an output file.")

    # Add arguments
    parser.add_argument("input_file", type=str, help="Path to the input file")
    parser.add_argument("output_file", type=str, help="Path to the output file")

    # Parse arguments
    args = parser.parse_args()

    # Print the received arguments (for debugging)
    print(f"Input file: {args.input_file}")
    print(f"Output file: {args.output_file}")

    process_pdfs(directory, pdf_list_file)


if __name__ == "__main__":
    main()


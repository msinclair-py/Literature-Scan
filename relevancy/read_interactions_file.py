from ast import literal_eval
import sys

def read_interactions_file(file_path):
    interactions = []
    with open(file_path, 'r') as file:
        for line in file:
            if line.strip() == 'None':
                continue
            if not line.startswith('[('):
                continue
            # Safely evaluate the Python literal expression
            line_data = literal_eval(line.strip())
            # If it's a single tuple, make it a list
            if isinstance(line_data, tuple):
                line_data = [line_data]
            interactions.extend(line_data)
    
    return interactions

# Example usage:
file_path = sys.argv[1]
interactions = read_interactions_file(file_path)

# Print to verify
for interaction in interactions:
    print(interaction)
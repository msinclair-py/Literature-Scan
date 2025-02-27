import pickle
import sys

results = sys.argv[1]
results = pickle.load(open(results, 'rb'))

for key, val in results.items():
    print(f'\nPMCID: {key}\n')
    print(f'Scored: {val["score"]}\nFocused summary: {val["response"]}\n')

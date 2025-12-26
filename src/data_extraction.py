#!/bin/python

import subprocess
import os
import json
from pathlib import Path

def get_program_index() -> dict:
    result = subprocess.check_output('apropos -l .', shell=True, text=True)

    # 'apropos', '(1)', '-', 'search', 'the', 'manual', 'page', 'names', 'and', 'descriptions'
    result_lines = result.split('\n')

    index_data = {}
    for line in result_lines:

        # 'apropos', '(1)', '-', 'search', 'the', 'manual', 'page', 'names', 'and', 'descriptions'
        program_entry = line.split(' ')
        program_entry = [i for i in program_entry if i != ''] # Remove whitespaces i.e. ['', '', '']

        if len(program_entry) == 0:
            continue
        
        # 'apropos'
        program_name = program_entry[0]

        # 'search', 'the', 'manual', 'page', 'names', 'and', 'descriptions'
        program_summary = ' '.join(program_entry[3:])

        index_data[program_name] = program_summary

    return index_data

def update_index(new_data: dict):
    json_data = json.dumps(new_data)
    
    data_folder_path = Path(__file__).parent / 'data'
    index_file_path = data_folder_path / 'index.json'

    with open(index_file_path, 'w') as file:
        file.write(json_data)


if __name__ == '__main__':
    data = get_program_index()
    
    print(f"Number of pages detected: {len(data)}")

    update_index(data)

    print('Written to "data/index.json"')

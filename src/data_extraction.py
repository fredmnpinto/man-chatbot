#!/bin/python

import re
import subprocess
import json
from pathlib import Path


SECTIONS_TO_LOOK_FOR_FLAGS = ['OPTIONS', 'OPTION', 'GLOBAL OPTIONS', 'COMMAND OPTIONS', 'POSITIONAL OPTIONS', 'FLAGS', 'SWITCHES']

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

def split_sections_of_man_page(page_content: str) -> dict:
    """
        Takes manual page content as a raw string and divide its sections into key-value pairs in a dict.
    """
    sections = {}
    current_section = "UNKNOWN"
    buffer = []

    for line in page_content.splitlines():
        # Found a section header
        if line.isupper() and len(line) < 40:

            # Completed current section
            if buffer:
                sections[current_section] = "\n".join(buffer).strip()

            # Start a new section
            current_section = line.strip()
            buffer = []
        else:
            buffer.append(line)

    # Close last section
    if buffer:
        sections[current_section] = "\n".join(buffer).strip()

    return sections


def get_man_page(program_name: str) -> dict:
    """
        Gets the man page for <program_name> and returns it as a dict with each section of the page as key value pairs.
    """
    page_content = subprocess.check_output(f"MANWIDTH=1000 man -P cat {program_name}", shell=True, text=True)

    split_page_content = split_sections_of_man_page(page_content)

    for section in split_page_content.keys():
        if section in SECTIONS_TO_LOOK_FOR_FLAGS:
            split_page_content[section] = split_options_in_section(split_page_content[section])

    return split_page_content

def split_options_in_section(section_content: str) -> dict:
    """
        Separates each flag in a page section into its own subdivided dict.
        Any content not specific to a single flag/option will be added to a subsection "CONTEXT"
    """
    section_lines = section_content.splitlines()
    option_header = None
    option_buffer = []

    result = {}
    result['CONTEXT'] = []


    for i in range(1, len(section_lines) - 1):
        line = section_lines[i]

        current_indent_level = count_indent_level(line)
        previous_level = count_indent_level(section_lines[i - 1])

        line_is_an_option_header = re.match(r'^\s*-\S+', line)

        # This line is no longer part of the option
        if current_indent_level < previous_level and option_header is not None:
            result[option_header] = '\n'.join(option_buffer)
            option_header = None
            option_buffer.clear()

        # Option header (i.e. --help This shows the guide on how to...)
        if line_is_an_option_header:
            split_header = line.split(maxsplit=1) # split first word (flag) from the rest (start of description)
            option_header = split_header[0]

            # The header may or may not include the start of the option/flag description on the header line
            if len(split_header) > 1:
                option_buffer = [split_header[1]] # Start of the description
            else:
                option_buffer = []
            continue

        # Not specific to a single option
        if option_header is None:
            if line == '' or line.isspace(): # Line is nothing but whitespaces
                continue

            result['CONTEXT'].append(line.strip())
            continue

        # Inside an option
        if current_indent_level >= previous_level and option_header is not None:
            option_buffer.append(line)
            continue

    return result

def count_indent_level(line: str) -> int:
    """
        Counts how many spaces there are in the beginning of a line.
    """
    level = 0

    for c in line:
        if c == ' ':
            level += 1
        else:
            return level

    return level

def save_man_page(program_name: str, page: dict) -> None:
    """
        Saves the program's man page contents onto data/pages/<program_name>.json
    """
    data_folder_path = Path(__file__).parent.parent / 'data'
    index_file_path = data_folder_path / 'pages' / f"{program_name}.json"

    with open(index_file_path, 'w') as file:
        file.write(json.dumps(page))

    print(f"Finished saving {program_name}")

if __name__ == '__main__':
    page_content = get_man_page('find')

    print(f"Sections: {page_content.keys()}")

    save_man_page('find', page_content)

    print('Finished')


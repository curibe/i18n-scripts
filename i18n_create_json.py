import json
import click
import re
import glob
import subprocess
from pathlib import Path
from bs4 import BeautifulSoup
from tabulate import tabulate
from colorama import Fore, Style
from collections import OrderedDict,Counter
import pdb


def read_file(filename):
    with open(filename, "r") as fstream:
        content = fstream.read()
    return content


def write_file(filename, content):
    with open(filename, "w") as f:
        f.write(content)


def read_json(filename):
    with open(filename, "r") as f:
        content = json.loads(f.read())
    return content


def write_json(filename, data):
    with open(filename, "w") as f:
        f.write(json.dumps(data, indent=4))


def show_table(datadict, color, fmt="pretty"):
    print(color)
    print(tabulate(datadict, headers="keys", tablefmt=fmt))
    print(Style.RESET_ALL)


def print_info(datadict, color, title=''):
    print(color)
    print(f"+{title:-^60s}+")
    print(json.dumps(datadict, indent=4))
    print(f"+{'':-^60s}+")
    print(Style.RESET_ALL)


def create_json_i18n(filename,json_content,verbose=False):
    content = read_file(filename)
    soup = BeautifulSoup(content, 'html.parser')
    matches = soup.find_all([], {"data-i18n": True})
    oldfields = set(json_content)

    for tag in matches:
        if not json_content.get(tag.get("data-i18n"), None):
            json_content.update({f"{tag.get('data-i18n')}": ''})
    
    newfields = {
        key
        for key in json_content.keys() if key not in oldfields
    }
    if verbose:
        show_table({
            "file": [Path(filename).name],
            "existing fields": oldfields,
            "new fields": newfields
        }, Fore.YELLOW)
        

def normalize(name):
    return name.replace("_", "-")


@click.group(context_settings={"token_normalize_func": normalize})
def cli():
    pass


@cli.command()
@click.option('-f',"--file")
@click.option('--output', '-o')
@click.option('-i', "--inplace", is_flag=True)
@click.option('-v',"--verbose",is_flag=True)
def onefile(**kwargs):
    filename = kwargs['file']
    trfile_content = {}
    verbose = kwargs["verbose"]

    outfile = Path(filename).parent.parent / "static/i18n" / kwargs['output']

    if outfile.exists():
        trfile_content = read_json(outfile)

    metadata = {"@metadata":trfile_content.pop("@metadata",None)}
    create_json_i18n(filename, trfile_content, verbose)
    trfile_content = {**metadata,**OrderedDict(sorted(trfile_content.items()))}
    
    if not kwargs["inplace"]:        
        print_info(
            trfile_content,
            Fore.LIGHTGREEN_EX,
            title=f"New content for {kwargs['output']}"
        )
    else:
        write_json(outfile, trfile_content)



@cli.command()
@click.option('-p',"--pattern")
@click.option('--output', '-o')
@click.option('-i', "--inplace", is_flag=True)
@click.option('-v',"--verbose",is_flag=True)
def severalfiles(**kwargs):
    pattern = kwargs['pattern']
    verbose = kwargs["verbose"]

    trfile_content = {}
    outfile = Path(pattern).parent.parent / "static/i18n" / kwargs['output']

    if outfile.exists():
        trfile_content = read_json(outfile)

    metadata = {"@metadata":trfile_content.pop("@metadata",None)}
    files = glob.glob(pattern)
    for file in files:
        create_json_i18n(file, trfile_content, verbose)
    
    trfile_content = {**metadata,**OrderedDict(sorted(trfile_content.items()))}
    
    if not kwargs["inplace"]:
        print_info(
            trfile_content,
            Fore.LIGHTGREEN_EX,
            title=f"New content for {kwargs['output']}"
        )
    else:
        write_json(outfile, trfile_content)


@cli.command()
@click.option('--path',required=True)
def check_duplicates(**kwargs):
    path = kwargs["path"]
    files = glob.glob(path)
    rx = re.compile(r'(data-i18n\b=\"([^"]*)\")')
    content = []
    for file in files:
        string = read_file(file)
        matches=rx.finditer(string)
        for match in matches:
            content.append(match.group(2))

    duplicates = [key for key,val in Counter(content).items() if val>1]

    show_table(
        {"KEY DUPLICATES": duplicates if duplicates else ["There are not duplicated keys"]},
        color=Fore.LIGHTRED_EX,
        fmt="simple"
    )


if __name__ == '__main__':
    cli()

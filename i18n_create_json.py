import json
import click
from pathlib import Path
from bs4 import BeautifulSoup
from tabulate import tabulate
from colorama import Fore, Style


def read_file(filename):
    with open(filename, "r") as fstream:
        content = fstream.read()
        fstream.seek(0, 0)
        content_by_lines = fstream.readlines()
    return content, content_by_lines


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


@click.group()
def cli():
    pass


@cli.command()
@click.argument('filename')
@click.option('--output', '-o')
@click.option('-i', "--inplace", is_flag=True)
def findtags(**kwargs):
    filename = kwargs['filename']
    trfile_content = {}

    outfile = Path(filename).parent.parent / "static/i18n" / kwargs['output']

    if outfile.exists():
        trfile_content = read_json(outfile)

    content, _ = read_file(filename)

    soup = BeautifulSoup(content, 'html.parser')

    matches = soup.find_all(["h1", "h2", "h3"], {"data-i18n": True})

    oldfields = set(trfile_content)

    for tag in matches:
        if not trfile_content.get(tag.get("data-i18n"), None):
            trfile_content.update({f"{tag.get('data-i18n')}": ''})

    newfields = {
        tag.get("data-i18n")
        for tag in matches if tag.get("data-i18n") not in oldfields
    }

    show_table({
        "existing fields": oldfields,
        "new fields": newfields
    }, Fore.LIGHTBLUE_EX)

    if not kwargs["inplace"]:
        print_info(
            trfile_content,
            Fore.LIGHTGREEN_EX,
            title=f"New content for {kwargs['output']}"
        )
    else:
        write_json(outfile, trfile_content)


if __name__ == '__main__':
    cli()

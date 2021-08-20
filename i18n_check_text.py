import click
import re
from bs4 import BeautifulSoup
from pathlib import Path
from tabulate import tabulate
from colorama import Fore, Style
import itertools as it


def read_file(filename):
    with open(filename, "r") as fstream:
        content = fstream.read()
        fstream.seek(0, 0)
        content_by_lines = fstream.readlines()
    return content, content_by_lines


def write_file(filename, content):
    with open(filename, "w") as f:
        f.write(content)


def show_table(datadict, color, fmt="pretty"):
    print(color)
    print(tabulate(datadict, headers="keys", tablefmt=fmt))
    print(Style.RESET_ALL)


def filter_text(regex, soup, content_by_lines):
    all_texts = soup.find_all(text=re.compile(regex))
    filtered_text = [
        x.strip("\n").split("\n")
        for x in all_texts
        if not any(ch in x for ch in ["{{", "{%"])
    ]
    filtered_text = list(it.chain.from_iterable(filtered_text))  # flat the list
    linenumbers = [
        [
            i for i, elm in enumerate(content_by_lines)
            if text in elm
        ]

        for text in filtered_text
    ]
    return filtered_text, linenumbers


@click.group()
def cli():
    pass


@cli.command()
@click.argument('filename')
@click.option('--show', is_flag=True)
@click.option('--replace', is_flag=True)
@click.option('--showcontext', is_flag=True)
def show(**kwargs):
    filename = kwargs["filename"]

    content, content_by_lines = read_file(filename)

    soupini = BeautifulSoup(content, 'html.parser')
    filtered_text, linenumbers = filter_text(
        r"[\n]{2}([(]*[\w ]+)", soupini, content_by_lines
    )

    show_table({
        "# line": linenumbers,
        f"{Path(filename).name}: text filtered": filtered_text}, Fore.YELLOW)

    context = [
        "".join(content_by_lines[line[0]-3:line[0]+3])
        for line in linenumbers
    ]

    if kwargs["showcontext"]:
        print(Fore.GREEN)
        print(f"+{'CONTEXT':-^98s}+")
        for text in context:
            print(text)
            print("-"*100)
        print(Style.RESET_ALL)


if __name__ == '__main__':
    cli()

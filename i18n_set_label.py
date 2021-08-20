import re
import click
from bs4 import BeautifulSoup
from tabulate import tabulate
from colorama import Fore, Style

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

def read_file(filename):
    with open(filename, "r") as fstream:
        content = fstream.read()
    return content


def write_file(filename, content):
    with open(filename, "w") as f:
        f.write(content)


@click.group(context_settings=CONTEXT_SETTINGS)
def cli():
    pass


@cli.command()
@click.argument('filename')
@click.option('--showfinal', is_flag=True, help="to show the insertion in dry run way")
@click.option('--replace', is_flag=True, help='to insert the data-i18n attr in-place')
def show(**kwargs):
    filename = kwargs["filename"]

    content = read_file(filename)
    new_content = content[:]

    alltags = [
        x.group() for x in re.finditer(
            r"<(h1|h2|h3)[^>]*\sid\b=\"([^\"]*)\"[^>]*>",
            content,
            re.MULTILINE | re.DOTALL
        )
    ]
    headers_without_id = [
        [x.group(), x.group(1), x.group(3)]
        for x in re.finditer(
            r"(<(h1|h2|h3)>)([\w ]*)",
            content,
            re.MULTILINE | re.DOTALL
            )
    ]

    print(Fore.GREEN)
    print(tabulate(
        {"regex: headers with id": alltags},
        tablefmt="pretty",
        headers="keys"
        )
    )
    print(tabulate(
        {"regex: headers without id": headers_without_id},
        tablefmt="pretty",
        headers="keys"
        ),
        Style.RESET_ALL
    )

    soupini = BeautifulSoup(content, 'html.parser')

    matches = soupini.find_all(["h1", "h2", "h3"], id=re.compile(".+"))
    print(Fore.BLUE)
    print(tabulate(
        {"bs4": matches},
        tablefmt="plain",
        headers=[f"+{'bs4: with id':-^100s}+"],
        colalign=("left",)
        )
    )
    print(Style.RESET_ALL)

    for tag in alltags:
        if ('"h1"' not in tag):
            if ("data-i18n" not in tag):
                tagbs4 = BeautifulSoup(tag, 'html.parser')
                datai18n_text = tagbs4.contents[0].get("id").replace("-header", "")
                newtag = f"{tag[:-1]} data-i18n=\"{datai18n_text}\">"
                new_content = new_content.replace(tag, newtag)

    if headers_without_id:
        for elm in headers_without_id:
            tag = elm[0]
            id_clousure = tag.find(">")
            # import pdb; pdb.set_trace()
            newtag = f"{tag[:id_clousure]} data-i18n=\"{elm[2].lower().replace(' ','-')}\">{elm[2]}"
            new_content = new_content.replace(elm[0], newtag)

    if kwargs["showfinal"]:
        print(Fore.YELLOW)
        print(f"{'bs4':^30s}")
        print(f'{"-"*30}')
        print(new_content)
        print(Style.RESET_ALL)

    if kwargs["replace"]:
        write_file(filename, new_content)

    # for elm in matches:
    #     if elm.get("id") != "h1":
    #         elm.attrs['data-i18n'] = elm.get("id")
    # print(Fore.GREEN, soup, Style.RESET_ALL)
    # modified_source = soup.encode(formatter=soup.original_encoding)
    # import pdb; pdb.set_trace()
    # with open("output.html", "wb") as file:
    #     file.write(modified_source)


if __name__ == '__main__':
    cli()

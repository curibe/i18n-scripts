import re
import os
import click
from bs4 import BeautifulSoup
from tabulate import tabulate
from colorama import Fore, Style
from pathlib import Path
import subprocess
import pdb

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


def read_file(filename):
    with open(filename, "r") as fstream:
        content = fstream.read()
    return content


def write_file(filename, content):
    with open(filename, "w") as f:
        f.write(content)

def show_table(content, color, fmt='pretty', header="keys",colalign=None):
    print(color)
    print(tabulate(
        content,
        headers=header,
        tablefmt=fmt,
        colalign=colalign
    ))
    print(Style.RESET_ALL)

def print_header(content,color):
    print(color)
    print(f"{content.center(120,'=')}")
    print(Style.RESET_ALL)

def print_info(content,title,color,type='text'):
        print(color)
        print(title)
        print(f'{"-"*30}')
        if type=='text':
            print(content)
        if type=='json':
            print(json.dumps(content, indent=4))
        print(Style.RESET_ALL)

def show_diff(filename):
    file=Path(filename)
    basename = file.parent.as_posix()
    name = file.name
    os.chdir(basename)

    print_header(" GIT STATUS ", Fore.MAGENTA)
    subprocess.run(["git","status"])
    
    print_header(f" GIT DIFF: {name} ", Fore.MAGENTA)
    subprocess.run(["git","--no-pager","diff", name])


@click.group(context_settings=CONTEXT_SETTINGS)
def cli():
    pass


@cli.command()
@click.argument('filename')
@click.option('--showfinal', '-sf', is_flag=True, help="to show the insertion in dry-run way")
@click.option('--replace', is_flag=True, help='to insert the data-i18n attr in-place')
@click.option('--show-diff','-sd', is_flag=True,help="to show the git status and diff of file changed")
@click.option('--overwrite','-ow',is_flag=True,help="to overwrite the data-i18n attr on files changed")
def show(**kwargs):
    """
    To check all tags h1,h2,h3 tags and insert attr 'data-i18n'

    This command allows to check all h1, h2 and h3 tags inside a html file and
    show/insert the attribute 'data-i18n' for internationalization.

    HOW TO USE 
    
    ===========

     1. For showing how could the final verion be after the insertion: 

        $ python i18n_set_label.py show path/to/file/<filename>.html -sf/--showfinal

    2. For doing the insertion in-place: 

        $ python i18n_set_label.py show path/to/file/<filename>.html --replace -sd/--show-diff

        where the option -sd is used to show the git status and git diff of the file changed

    """
    filename = kwargs["filename"]
    name = Path(filename).stem.replace("_","-").lower()

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

    print_header(f' FIND TAGS AND COMPARING IN {Path(filename).name}  ', Fore.LIGHTCYAN_EX)

    show_table({"regex: headers with id": alltags}, Fore.GREEN)
    show_table({"regex: headers without id": headers_without_id}, Fore.GREEN)
    
    soupini = BeautifulSoup(content, 'html.parser')

    matches = soupini.find_all(["h1", "h2", "h3"], id=re.compile(".+"))
    show_table({"bs4": matches},
               Fore.BLUE,
               fmt="plain",
               header=[f"+{'bs4: with id':-^100s}+"]
    )
   
    for tag in alltags:
        if ('"h1"' not in tag):
            tagbs4 = BeautifulSoup(tag, 'html.parser')
            tag_content = tagbs4.contents[0]
            if not kwargs["overwrite"]:
                if ("data-i18n" not in tag):
                    datai18n_text = tag_content.get("id").replace("-header", "").lower()
                    newtag = f"{tag[:-1]} data-i18n=\"{name}-{datai18n_text}\">"
                    new_content = new_content.replace(tag, newtag)
            else:
                datai18n_text = tag_content.get("id").replace("-header", "").lower()
                
                if not tag_content.has_attr("data-i18n"):
                    newtag = f"{tag[:-1]} data-i18n=\"{name}-{datai18n_text}\">"
                    new_content = new_content.replace(tag, newtag)
                else:
                    datai18n_content = tag_content.get("data-i18n")
                    oldattr = f"data-i18n=\"{datai18n_content}\""
                    newattr = f"data-i18n=\"{name}-{datai18n_text}\""
                    new_content = new_content.replace(oldattr, newattr)

            

    if headers_without_id:
        for elm in headers_without_id:
            tag = elm[0]
            id_clousure = tag.find(">")
            # import pdb; pdb.set_trace()
            newtag = f"{tag[:id_clousure]} data-i18n=\"{name}-{elm[2].lower().replace(' ','-')}\">{elm[2]}"
            new_content = new_content.replace(elm[0], newtag)

    if kwargs["showfinal"]:
        print_header(" RESULT ",Fore.MAGENTA)
        print_info(new_content, f"{'with bs4':^30s}", Fore.YELLOW)

    if kwargs["replace"]:
        write_file(filename, new_content)

    if kwargs["show_diff"]:
        show_diff(filename)


@cli.command()
@click.argument('filename')
@click.option('--showfinal', '-sf', is_flag=True, help="to show the insertion in dry-run way")
@click.option('--replace', is_flag=True, help='to insert the data-i18n attr in-place')
@click.option('--show-diff','-sd', is_flag=True,help="to show the git status and diff of file changed")
def overwrite(**kwargs):
    filename = kwargs["filename"]
    name = Path(filename).stem.replace("_","-").lower()

    content = read_file(filename)
    new_content = content[:]

    print_header(f' FOUND TAGS IN {Path(filename).name} ', Fore.LIGHTCYAN_EX)

    soupini = BeautifulSoup(content, 'html.parser')
    matches = soupini.find_all(["h1", "h2", "h3"], {"data-i18n": True})
    show_table({"bs4": matches},
               Fore.BLUE,
               fmt="plain",
               header=[f"+{'bs4: with id':-^100s}+"]
    )

    for match in matches:
        datai18n_text = match.get("data-i18n")
        oldattr = f"data-i18n=\"{datai18n_text}\""
        if datai18n_text.startswith(f"{name}-"):
            print(f"{datai18n_text} --> Nothing to change....")
        else:
            newattr = f"data-i18n=\"{name}-{datai18n_text.lower()}\""
            print(f"{oldattr} --> {newattr}")
            new_content = new_content.replace(oldattr, newattr)

    if kwargs["showfinal"]:
        print_header(" RESULT ",Fore.MAGENTA)
        print_info(new_content, f"{' New content':^30s}", Fore.YELLOW)

    if kwargs["replace"]:
        write_file(filename, new_content)

    if kwargs["show_diff"]:
        show_diff(filename)

@cli.command()
@click.argument('filename')
def showdiff(filename):
    """
    To show git status/diff of file changed

    This command allows to show the git status and git diff of the file chnged

    HOW TO USE 
    
    ===========

    1. For show the git status and git diff of the file changed

        $ python i18n_set_label.py showdiff path/to/file/filename.html


    """
    show_diff(filename)



if __name__ == '__main__':
    cli()

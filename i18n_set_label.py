import re
import os
import click
from bs4 import BeautifulSoup
from tabulate import tabulate
from colorama import Fore, Style
from pathlib import Path
from operator import itemgetter
import subprocess
import textwrap
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

def print_message(content, color, fmt):
    print(color)
    print(tabulate(
        content,
        headers="keys",
        tablefmt=fmt
    ))
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

def replace_new_tag(kwargs):
    name, attr_text, pattern, content, new_content = (
        itemgetter(
            "name",
            "attr_text", 
            "pattern", 
            "content",
            "new_content"
            )(kwargs)
    )
    matches = re.finditer(pattern, content)
    for match in matches:
        oldtag = match.group(0)
        idx = re.search(">",oldtag).span()[0]
        newtag = f"{oldtag[:idx]} data-i18n=\"{name}-{attr_text}\"{oldtag[idx:]}"
        new_content = new_content.replace(oldtag, newtag) 
    return new_content


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

    soupini = BeautifulSoup(content, 'html.parser')

    headers_with_id = soupini.find_all(["h1", "h2", "h3", "h4"], {"id":True})
    headers_without_id = soupini.find_all(["h1", "h2", "h3", "h4"], {"id":False})

    show_table({"Headers with id": headers_with_id}, Fore.GREEN)
    show_table({"Headers without id": headers_without_id}, Fore.GREEN)

    for tag in headers_with_id:
        if tag.get("id") != "h1":
            id_text = tag.get("id")
            datai18n_text = id_text.replace("-header","").lower()
            if not tag.has_attr("data-i18n"):
                 pattern = r"(<{}[^>]*\sid\b=\"{}\"[^>]*>)".format(tag.name,tag.get("id"))
                 new_content = replace_new_tag({
                     "name":name,
                     "pattern":pattern,
                     "content":content,
                     "new_content":new_content,
                     "attr_text":datai18n_text
                 })             
            else:
                print_message({
                        "FILENAME": [filename],
                        "TAG: " : [textwrap.fill(str(tag), width=60)],
                        "INFO": ["Nothing to change"]
                    }, 
                    Fore.LIGHTRED_EX, "simple"
                )

   
    for tag in headers_without_id:
        if tag.attrs:
            if not tag.has_attr("data-i18n"):

                attrs_name = list(tag.attrs.keys())
                attrs_vals = list(tag.attrs.values())
                datai18n_text = tag.text.lower().strip().replace(" ","-")
                pattern = r"(<{}[^>]*\s{}\b=\"{}\"[^>]*>{})".format(
                    tag.name, attrs_name[0], " ".join(attrs_vals[0]), tag.text
                )
                new_content = replace_new_tag({
                        "name":name,
                        "pattern":pattern,
                        "content":content,
                        "new_content":new_content,
                        "attr_text":datai18n_text
                })
            else:
                print_message({
                        "FILENAME": [filename],
                        "TAG: " : [textwrap.fill(str(tag), width=60)],
                        "INFO": ["Nothing to change"]
                    }, 
                    Fore.LIGHTRED_EX, "simple"
                )
        else:
            datai18n_text = tag.text.lower().strip().replace(" ","-")
            pattern = r"(<{}>{})".format(tag.name, tag.text)
            new_content = replace_new_tag({
                        "name":name,
                        "pattern":pattern,
                        "content":content,
                        "new_content":new_content,
                        "attr_text":datai18n_text
            })


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
    matches = soupini.find_all(["h1", "h2", "h3", "h4"], {"data-i18n": True})
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

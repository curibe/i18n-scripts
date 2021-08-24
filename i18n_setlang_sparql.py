import re
import click
from tabulate import tabulate
from colorama import Fore, Style
from pathlib import Path
import textwrap
import subprocess
import pdb

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


def print_info(content, color, fmt):
    print(color)
    print(tabulate(
        content,
        headers="keys",
        tablefmt=fmt
    ))
    print(Style.RESET_ALL)

def replace_with_sed(filename, old, new, inplace=False):
    new = new.replace("{{","\{\{").replace("}}","\}\}")
    if inplace:
        cmd =[
            "sed",
            "-i",
            f"s/{old}/{new}/g",
            f"{filename}"
        ]
        psed = subprocess.run(cmd, stdout=subprocess.PIPE)
        pcat = subprocess.Popen(["cat", filename], stdout=subprocess.PIPE)
        # pdb.set_trace()
        pgrep = subprocess.Popen(
                ["grep", "g.lang_code", "-n"],
                stdin=pcat.stdout,
                stdout=subprocess.PIPE
        )
        pcat.stdout.close()
        replacement = pgrep.communicate()[0]

    else:
        cmd =[
            "sed",
            f"s/{old}/{new}/g",
            f"{filename}"
        ]

        psed = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        pgrep = subprocess.Popen(
                ["grep", "g.lang_code", "-n"],
                stdin=psed.stdout,
                stdout=subprocess.PIPE
        )
        psed.stdout.close()
        replacement = pgrep.communicate()[0]
    return replacement


@click.group(context_settings=CONTEXT_SETTINGS)
def cli():
    pass


@cli.command()
@click.argument('filename')
@click.option('--inplace',is_flag=True)
def findreplace(**kwargs):
    filename = kwargs["filename"]

    process = subprocess.run(['cat',filename],stdout=subprocess.PIPE)
    re_obj = re.compile(r'(wikibase:language )("([^"]*)")')
    matches = re_obj.search(process.stdout.decode('utf-8'))
    languages = matches.group(3)
    newlang = languages

    have_langcode = "g.lang_code" in languages
    have_autolang = "[AUTO_LANGUAGE]" in languages

    if not have_autolang:
        newlang = f"[AUTO_LANGUAGE],{newlang}"

    if not have_langcode:
        newlang = f"{{{{ g.lang_code }}}},{newlang}"

    if not (have_langcode or have_autolang):
        replacement=replace_with_sed(filename, languages, newlang, inplace=kwargs["inplace"])
        print_info({
            "Filename": [Path(filename).name], 
            "Text that will be replaced\n( nline: newtext )": [
                textwrap.fill(replacement.decode('utf-8'), width=50)
            ]
        }, Fore.LIGHTGREEN_EX, "psql")
    else:
        print_info({"INFO: " : ["Nothing to change"]}, Fore.LIGHTRED_EX, "plain")



if __name__ == '__main__':
    cli()

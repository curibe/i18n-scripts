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

def check_and_set_word_order(string,words):
    string_list = string.split(",")
    
    for i,word in enumerate(words):
        onlyword = re.sub(r'[\{\}\[\] ]','',word)
        if word in string_list:
            string_list.remove(word)
        elif onlyword in string:
            idx = [ i for i,s in enumerate(string_list) if onlyword in s]
            string_list = [ elm for i,elm in enumerate(string_list) if i not in idx]
                
        string_list.insert(i,word)
    return ','.join(string_list)

def set_filter_lang(match,word):
    lang = match.group(2)
    line = match.group(1)
    newline = re.sub(lang,f"'{word}'",line)
    return newline

    

def replace_with_sed(filename, old, new, inplace=False, text_to_find='g.lang_code'):
    # rx = re.compile("([\{\}\[\]])")
    new = re.escape(new)
    old = re.escape(old)
    if inplace:
        cmd =[
            "sed",
            "-i",
            "-r",
            f"s/{old}/{new}/g",
            f"{filename}"
        ]
        psed = subprocess.run(cmd, stdout=subprocess.PIPE)
        pcat = subprocess.Popen(["cat", filename], stdout=subprocess.PIPE)
        # pdb.set_trace()
        pgrep = subprocess.Popen(
                ["grep", text_to_find, "-n"],
                stdin=pcat.stdout,
                stdout=subprocess.PIPE
        )
        pcat.stdout.close()
        replacement = pgrep.communicate()[0]

    else:
        cmd =[
            "sed",
            "-r",
            f"s/{old}/{new}/g",
            f"{filename}"
        ]

        psed = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        pgrep = subprocess.Popen(
                ["grep", text_to_find, "-n"],
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
@click.option('--inplace',"-i",is_flag=True)
def findreplace(**kwargs):
    filename = kwargs["filename"]

    process = subprocess.run(['cat',filename],stdout=subprocess.PIPE)
    re_obj = re.compile(r'(wikibase:language[\s]+)("([^"]*)")')
    matches = re_obj.search(process.stdout.decode('utf-8'))
    # pdb.set_trace()
    if matches:
        languages = matches.group(3)
        newlang = languages
        newlang = check_and_set_word_order(languages, [
            "{{ g.lang_code }}",
            "[AUTO_LANGUAGE]",
            "en"
        ])
        

        if newlang != languages:
            
            if "," not in languages:
                languages = f'{matches.group(1)}{matches.group(2)}'
                newlang=f'{matches.group(1)}"{newlang}"'
            
            replacement=replace_with_sed(filename, languages, newlang, inplace=kwargs["inplace"])
            print_info({
                "Filename": [Path(filename).name], 
                "Text that will be replaced\n( nline: newtext )": [
                    textwrap.fill(replacement.decode('utf-8'), width=50)
                ]
            }, Fore.LIGHTGREEN_EX, "psql")
        else:
            print_info({"INFO: " : ["Nothing to change"]}, Fore.LIGHTRED_EX, "plain")
    else:
        print_info({
            "WARNING: ": [f"The file '{Path(filename).name}' not has language option inside"]
            }, 
            Fore.LIGHTYELLOW_EX, "plain")

@cli.command()
@click.argument('filename')
@click.option('--inplace',"-i",is_flag=True)
def filterlang(**kwargs):
    filename = kwargs["filename"]

    process = subprocess.run(['cat',filename],stdout=subprocess.PIPE)
    re_obj = re.compile(r"(FILTER[\s]*\(LANG\(\?\w*\)[\s=]*([\"']([^'\"]*)[\"'])\))")
    matches = re_obj.search(process.stdout.decode('utf-8'))
    # pdb.set_trace()
    if matches:
        oldline = matches.group(1)
        newline = set_filter_lang(matches, "{{ g.lang_code }}")

        if newline != oldline:
            replacement=replace_with_sed(
                filename,oldline, newline,
                inplace=kwargs["inplace"],
                text_to_find="FILTER.*g.lang_code")
            print_info({
                "Filename": [Path(filename).name], 
                "Text that will be replaced\n( nline: newtext )": [
                    '\n'.join(line.strip() for line in re.findall(r'.{1,90}(?:\s+|$)', replacement.decode('utf-8')))
                    # textwrap.fill(replacement.decode('utf-8'), width=100)
                ]
            }, Fore.LIGHTGREEN_EX, "psql")
        else:
           print_info({"INFO: " : ["Nothing to change"]}, Fore.LIGHTRED_EX, "plain") 

    else:
         print_info({
            "WARNING: ": [f"The file '{Path(filename).name}' not has FILTER LANG inside"]
            }, 
            Fore.LIGHTYELLOW_EX, "plain")



if __name__ == '__main__':
    cli()

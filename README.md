# i18n-scripts

These scripts can be used to implement internazionalitation with
jquery.i18n in a html file 

There are 3 main scripts:

 - **i18n_set_label.py**: Check all headers inside the html file and create
   an attribute `data-i18n` in it with the same content in `id` attribute. In case on the header don't have an `id`, the content of `data-i18n` will be the text between the header tag.
 - **i18n_check_text.py**[WIP]: This script look for text without tags
 - **i18n_create_json.py**: This script search for every tag with the attribute `data-i18n`inside the html file and create a json file with the content of `data-i18n`.


## Dependencies
This scripts use the following dependencies
 - colorama
 - Beautifulsoup
 - tabulate
 - re
 - click
 ## How to use

 ### To show all tags/headers with and without id
 ```python
 python i18n_set_label.py show path/to/file.html
 ```
 ### To show the final version after insert label in dry-run way
```python
 python i18n_set_label.py show path/to/file.html --showfinal
```

 ### To replace the html with the new version with i18n attr
```python
 python i18n_set_label.py show path/to/file.html --replace
```

 ### To find tags with attribute `data-i18n`
 This command require to pass the json filename
```python
 python i18n_create_json.py findtags path/to/<file>.html -o <lang>.json 
```

 ### To find tags with attribute `data-i18n` and create/update file in-place
 This command require to pass the json filename
```python
 python i18n_create_json.py findtags path/to/<file>.html -o <lang>.json --inplace
```
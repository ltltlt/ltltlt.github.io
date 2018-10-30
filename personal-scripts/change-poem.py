'''''''''''''''''''''''''''''''''''''''''''''''''''
  > System:		Arch
  > Author:		ty-l8
  > Mail:		liuty196888@gmail.com
  > File Name:		change-poem.py
  > Created Time:	2018-10-30 二 22:43
'''''''''''''''''''''''''''''''''''''''''''''''''''

import re
import os
import sys

base = os.path.join(os.path.dirname(__file__), '../')
poem_history_dir = os.path.join(base, "poem-history")
file = os.path.join(base, 'index.md')

def get_input():
    title = input('title: ').strip()+'   '
    author = input('author: ').strip()
    body = '\n'.join(line.strip()+'   ' for line in sys.stdin)  # make markdown change line
    return title, author, body

def save(title, author, body):
    if title:
        file = title
    elif body:
        file = body[:10].replace('\n', '-').replace('/', '-')
    if not file:
        file = 'any'
    if not os.path.exists(poem_history_dir):
        os.mkdir(poem_history_dir)
    file = os.path.join(poem_history_dir, file)
    while os.path.exists(file):
        file += '_'
    with open(file, 'w') as f:
        print('title:', title, file=f)
        print('author:', author, file=f)
        print(body, file=f)
def main():
    title, author, body = get_input()

    format_ = r'''
    ---
    ## A poem a day, keeps foolish away.
    > {}
    > {}
    ---<cite>{}</cite>
    ---
    '''.strip()
    format_ = r'\n'.join(l.strip() for l in format_.split('\n'))
    r = re.compile(format_.format(r'([^\n]*?)', r'([\s\S]*?)', r'([^>]*?)'))
    with open(file) as f:
        content = f.read()
    matches = r.search(content)
    old_title, old_body, old_author = matches.groups()
    old_title = old_title.strip()
    old_body = old_body.strip()
    old_author = old_author.strip()
    save(title=old_title, author=old_author, body=old_body)
    content = r.sub(format_.format(title, body, author), content)
    with open(file, 'w') as f:
        f.write(content)

if __name__ == '__main__':
    try: 
        main()
    except KeyboardInterrupt:
        pass

import os
import re
import requests
from pathlib import Path
from bs4 import BeautifulSoup

from aventine.library.utils import randkey


def split_title(title):
    title = title.strip()
    splits = title.split('\n')
    splits = [i.strip() for i in splits]
    title = ' '.join(splits[:-1]).strip()
    info = splits[-1].strip()
    return title, info


def get_perseus_xml(text_url,
                    save_dir,
                    existing_keys=[],
                    stem='https://www.perseus.tufts.edu/hopper/'):
    save_dir = Path(save_dir)
    os.makedirs(save_dir, exist_ok=True)

    text_data = requests.get(text_url)
    soup = BeautifulSoup(text_data.content, 'html.parser')
    group = soup.find('p', attrs={'class': 'xml_download'})
    xml_url = stem + group.find('a')['href']

    title, info = split_title(soup.find('div', attrs={'id': 'header_text'}).text)

    xml_data = requests.get(xml_url)
    _key = randkey(existing_keys)
    with open(save_dir / f'{_key}.xml', "wb") as f:
        f.write(xml_data.content)

    return {'key': _key, 'title': title, 'info': info}


_whitespaces_expr = re.compile(r'\s+')

def perseus_xml2txt(input_fpath, output_fpath):
    with open(input_fpath, 'r', encoding='utf-8') as f:
        sgml_data = f.read()
    
    soup = BeautifulSoup(sgml_data, features="xml")
    body = soup.find('body')
    collated = ''

    for chapter in body.find_all(attrs={'type': 'chapter'}):
        text = re.sub(_whitespaces_expr, ' ', chapter.text)
        text = text.strip()
        collated += text + '\n'
    
    with open(output_fpath, 'w', encoding='utf-8') as f:
        f.write(collated.strip())

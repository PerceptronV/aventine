import os
import re
import json
import requests
import unicodedata
from pathlib import Path
from urllib.parse import unquote
from bs4 import BeautifulSoup
from bs4.element import Tag


from aventine.library.config import SMALL_SEP, CHUNK_SEP
from aventine.library.config import ALLOWED_SYMBOLS, ALLOWED_PUNCTS


def perseus_collect(
    url: str = 'https://www.perseus.tufts.edu/hopper/collection?collection=Perseus:corpus:perseus,Latin Texts'
):
    extract_text_id = lambda x : unquote(x).split(':')[-1]

    collection = requests.get(url)
    soup = BeautifulSoup(collection.content, 'html.parser')
    return {
        extract_text_id(link['href']): link.text.strip()
        for link in soup.find_all('a', attrs={'class': 'aResultsHeader'})
    }


def split_title(
    title: str
) -> tuple['title', 'info']:
    title = title.strip()
    splits = title.split('\n')
    splits = [i.strip() for i in splits]
    title = ' '.join(splits[:-1]).strip()
    info = splits[-1].strip()
    return title, info

def perseus_xml_get(
    text_id: str,
    save_dir: Path,
    existing_keys: list = [],
    text_stem: str = 'https://www.perseus.tufts.edu/hopper/text?doc=Perseus:text:{}',
    server_stem: str = 'https://www.perseus.tufts.edu/hopper/{}',
    overwrite: bool = False
) -> dict:
    
    save_dir = Path(save_dir)
    os.makedirs(save_dir, exist_ok=True)

    text_data = requests.get(text_stem.format(text_id))
    soup = BeautifulSoup(text_data.content, 'html.parser')
    group = soup.find('p', attrs={'class': 'xml_download'})
    xml_url = server_stem.format(group.find('a')['href'])

    title, info = split_title(soup.find('div', attrs={'id': 'header_text'}).text)
    schema_example = soup.find('input', attrs={'name': 'doc'})['value'].strip()
    schema = f"{'+'.join(schema_example.split(' ')[:-1])}+{{}}"

    xml_data = requests.get(xml_url)
    _key = text_id # randkey(existing_keys)
    fpath = save_dir / f'{_key}.xml'

    if overwrite or not os.path.exists(fpath):
        with open(fpath, "wb") as f:
            f.write(xml_data.content)

    return {
        'key': _key,
        'text_id': text_id,
        'schema': schema,
        'save_dir': str(save_dir),
        'xml_fpath': str(fpath),
        'title': title,
        'info': info
    }

def ext(id, new_ext):
    if id.strip() == '':
        return new_ext
    return f'{id}.{new_ext}'

def signature(tag):
    return (
        tag.name,
        tag['type'] if 'type' in tag.attrs else None,
        tag['unit'] if 'unit' in tag.attrs else None
    )


def normalise_text(text: str, allowed=ALLOWED_SYMBOLS):
    text = text.lower()
    text = unicodedata.normalize('NFKC', text)
    text = re.sub(rf'[^{allowed}]', '', text)
    text = re.sub(rf'([{ALLOWED_PUNCTS}])', r' \1 ', text)
    text = re.sub(r'[ ]+', ' ', text)
    text = text.strip()
    return text


_whitespaces = re.compile(rf'[{CHUNK_SEP}\r\t]+')

def linear_parse(
    body: Tag
) -> str:
    
    collated = ''
    index = []
    levels, signatures = [], []
    current_signature = None
    began = False
    written = False

    for element in body.find_all():
        if 'n' in element.attrs and element.name not in {'l'}:
            began = True
            written = False
            if signature(element) == current_signature:
                levels.pop()
                levels.append(element['n'])
            else:
                current_signature = signature(element)
                try:
                    end = signatures.index(current_signature)
                except:
                    end = len(signatures)
                levels = levels[:end] + [element['n']]
                signatures = signatures[:end] + [current_signature]
        
        else:
            new_text = re.sub(_whitespaces, ' ', element.text).strip()
            if began and new_text != '':
                if not written:
                    collated = collated.strip() + CHUNK_SEP
                    index.append('.'.join(levels))
                    written = True
                collated += new_text + SMALL_SEP

    return normalise_text(collated), index


def perseus_xml2txt(
    metadata: dict,
    save_dir: Path,
    overwrite: bool = False
) -> dict:
    
    save_dir = Path(save_dir)
    os.makedirs(save_dir / 'metadata', exist_ok=True)
    txt_path = save_dir / f"{metadata['key']}.txt"
    json_path = save_dir / 'metadata' / f"{metadata['key']}.json"
    
    if not overwrite and os.path.exists(json_path):
        with open(json_path, 'r') as f:
            return json.load(f)
    
    with open(metadata['xml_fpath'], 'r', encoding='utf-8') as f:
        xml_data = f.read()
    
    soup = BeautifulSoup(xml_data, features="xml")
    quick_extract = lambda x : soup.find(x).text.strip()

    title, author, editor = (quick_extract(i) for i in ('title', 'author', 'editor'))

    body = soup.find('body')
    collated, index = linear_parse(body)

    metadata.update({'title': title,
                     'author': author,
                     'editor': editor,
                     'txt_fpath': str(txt_path)})
    
    assert len(index) == len(collated.split(CHUNK_SEP))

    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(collated)
    with open(json_path, 'w', encoding='utf-8') as f:
        metadata |= {
            'len_index': len(index),
            'index': index
        }
        json.dump(metadata, f, indent=4)
    
    return metadata


def perseus_url(
    metadata: dict,
    quote_id: str,
    stem: str = "https://www.perseus.tufts.edu/hopper/text?doc={}&fromdoc=Perseus:text:{}"
) -> str:
    return stem.format(metadata['schema'].format(quote_id), metadata['text_id'])

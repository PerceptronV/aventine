import os
import re
import json
import requests
from pathlib import Path
from urllib.parse import unquote
from bs4 import BeautifulSoup
from bs4.element import Tag


from config import CHUNK_SEP
from config import QUICKSTART_DOCUMENTS
from utils import randkey


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
    server_stem: str = 'https://www.perseus.tufts.edu/hopper/{}'
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
    _key = randkey(existing_keys)
    with open(save_dir / f'{_key}.xml', "wb") as f:
        f.write(xml_data.content)

    return {
        'key': _key,
        'text_id': text_id,
        'schema': schema,
        'save_dir': str(save_dir),
        'xml_fpath': str(save_dir / f'{_key}.xml'),
        'title': title,
        'info': info
    }

def ext(id, new_ext):
    if id.strip() == '':
        return new_ext
    return f'{id}.{new_ext}'

_whitespaces = re.compile(r'[\n\r\t]+')

def recursive_parse(
    element: Tag,
    id: str,
    data: dict,
    root = True
) -> str:
    
    if element.name == 'milestone' and 'n' in element.attrs:
        data['text'] = data['text'].strip(' ') + CHUNK_SEP
        data['index'].append(ext(id, element['n']))
        return data

    if root or 'n' in element.attrs:
        id = ext(id, element['n']) if 'n' in element.attrs else id
        for ele in element.find_all(recursive=False):
            recursive_parse(ele, id, data, root=False)
        return data
    
    data['text'] += re.sub(_whitespaces, ' ', element.text).strip(' ') + ' '
    return data

def perseus_xml2txt(
    metadata: dict,
    save_dir: Path
) -> dict:
    
    with open(metadata['xml_fpath'], 'r', encoding='utf-8') as f:
        xml_data = f.read()
    
    soup = BeautifulSoup(xml_data, features="xml")
    quick_extract = lambda x : soup.find(x).text.strip()

    title, author, editor = (quick_extract(i) for i in ('title', 'author', 'editor'))

    data = {'text': '', 'index': []}
    body = soup.find('body')
    _ = recursive_parse(body, '', data, root=True)
    collated = re.sub(r'\n[ ]+', '\n', data['text']).strip()
    collated = re.sub(r'[ ]+', ' ', collated).strip()
    
    save_dir = Path(save_dir)
    os.makedirs(save_dir / 'metadata', exist_ok=True)

    metadata.update({'title': title,
                     'author': author,
                     'editor': editor,
                     'txt_fpath': str(save_dir / f"{metadata['key']}.txt")})
    
    assert len(data['index']) == len(collated.split(CHUNK_SEP))

    with open(save_dir / f"{metadata['key']}.txt", 'w', encoding='utf-8') as f:
        f.write(collated)
    with open(save_dir / 'metadata' / f"{metadata['key']}.json", 'w', encoding='utf-8') as f:
        json.dump(metadata | {
            'len_index': len(data['index']),
            'index': data['index']
        }, f, indent=4)
    
    return metadata


def perseus_url(
    metadata: dict,
    quote_id: str,
    stem: str = "https://www.perseus.tufts.edu/hopper/text?doc={}&fromdoc=Perseus:text:{}"
) -> str:
    return stem.format(metadata['schema'].format(quote_id), metadata['text_id'])

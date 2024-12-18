import re
from tqdm import tqdm
from pathlib import Path

import cltk
from cltk import NLP
from sentence_transformers import SentenceTransformer

from aventine.library.config import CHUNK_SEP
from aventine.library.config import ROOT_FINGERPRINT, CORPUS_FINGERPRINT
from aventine.library.config import ALLOWED_LEMMATA, BAD_LEMMATA
from aventine.library.config import SENTENCE_TRANSFORMER_MODEL as ENG_MODEL
from aventine.library.config import WORD_EMBEDDING_MODEL as LAT_MODEL
from aventine.library.utils import Checkpointer
from aventine.library.utils import meanings
from aventine.library.utils import strfseconds, get_null, replace_if_none


def preprocess(file_metadata,
               save_dir: Path,
               tool_dir: Path,
               eng_model: str = ENG_MODEL):
        
    lat_model = LAT_MODEL('lat')
    eng_model = SentenceTransformer(eng_model, trust_remote_code=True)
    lat_none, _ = get_null(lat_model, eng_model)
    
    text_fpath, save_dir = Path(file_metadata['txt_fpath']), Path(save_dir)
    name = file_metadata['title']
    key = file_metadata['key']
    
    cltk_nlp = NLP(language="lat")
    cltk_nlp.pipeline.processes = [
        cltk.alphabet.processes.LatinNormalizeProcess,
        cltk.dependency.processes.LatinStanzaProcess
    ]

    def run_pipeline(chunks):
        root_ckpt = Checkpointer(save_dir / 'root', ROOT_FINGERPRINT)
        corpus_ckpt = Checkpointer(save_dir / key, CORPUS_FINGERPRINT)
        c = corpus_ckpt.load()
        r = root_ckpt.load()

        if not c.meta:
            c.meta = {'total': len(chunks)}
            start = 0
            print(f'Starting from scratch.')
        else:
            start = c.meta['completed'] + 1
            print(f'Resuming from chunk {start}.')
        iter = tqdm(range(start, len(chunks)))
        iter.set_description(name)

        for chunk_index in iter:

            text = chunks[chunk_index]
            doc = cltk_nlp.analyze(text)

            new_lemmata, new_definitions, lemmatised = [], [], ''
            subbar = tqdm(zip(doc.lemmata, doc.pos, doc.tokens), leave=False)

            for _lemma, pos, tok in subbar:
                subbar.set_description(_lemma)

                if pos == 'PUNCT' or not re.fullmatch(ALLOWED_LEMMATA, _lemma) or _lemma in BAD_LEMMATA:
                    lemmatised += _lemma + ' '
                    continue

                www_lemma, www_meaning = meanings(tok, tool_dir=tool_dir)
                lemma = _lemma if www_lemma == '' else www_lemma
                _k = f'{lemma} ({pos})'

                if _k in r.existing_lemmata:
                    if key not in r.root_lemmata_info[_k]['texts']:
                        r.root_lemmata_info[_k]['texts'].add(key)
                        c.corpus_lemmata_info[_k] = {'count': 1, 'loc': [chunk_index]}
                    else:
                        c.corpus_lemmata_info[_k]['count'] += 1
                        c.corpus_lemmata_info[_k]['loc'].append(chunk_index)
                
                else:
                    r.existing_lemmata.add(_k)
                    r.root_lemmata_info[_k] = {'texts': {key}}
                    c.corpus_lemmata_info[_k] = {'count': 1, 'loc': [chunk_index]}

                    new_lemmata.append(lemma)
                    new_definitions.append(www_meaning)

            r.lemmatised += lemmatised.strip()               
            r.lemmata_arr.extend(new_lemmata)
            r.lat_embeddings.extend([
                replace_if_none(lat_model.get_word_vector(w), lat_none) for w in new_lemmata
            ])
            r.definitions.extend(new_definitions)
            r.eng_embeddings.extend(eng_model.encode(new_definitions))

            r.info['num_lemmata'] = len(r.root_lemmata_info)
            c.meta['num_lemmata'] = len(c.corpus_lemmata_info)
            c.meta['completed'] = chunk_index
            if iter.format_dict['rate'] is not None:
                c.meta['eta'] = '+' + strfseconds(
                    (iter.format_dict['total'] - iter.format_dict['n'] - 1) / iter.format_dict['rate']
                )
            
            assert r.info['num_lemmata'] == len(r.existing_lemmata) == len(r.lat_embeddings)
            
            root_ckpt.save(r)
            corpus_ckpt.save(c)
    
    with open(text_fpath, 'r', encoding='utf-8') as f:
        corpus = f.read()
    
    run_pipeline(corpus.split(CHUNK_SEP))

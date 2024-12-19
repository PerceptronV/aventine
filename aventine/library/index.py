import re
from tqdm import tqdm
from pathlib import Path

import cltk
from cltk import NLP
from sentence_transformers import SentenceTransformer

from aventine.library.config import CHUNK_SEP
from aventine.library.config import ROOT_FINGERPRINT, CORPUS_FINGERPRINT
from aventine.library.config import ALLOWED_LEMMATA, BAD_LEMMATA
from aventine.library.config_ml import SENTENCE_TRANSFORMER_MODEL as ENG_MODEL
from aventine.library.config_ml import WORD_EMBEDDING_MODEL as LAT_MODEL
from aventine.library.wordvec import train_word2vec_model
from aventine.library.utils import Checkpointer
from aventine.library.utils import meanings
from aventine.library.utils import strfseconds, get_null, replace_if_none


lat_model = LAT_MODEL('lat')
eng_model = SentenceTransformer(ENG_MODEL, trust_remote_code=True)
lat_none, _ = get_null(lat_model, eng_model)

cltk_nlp = NLP(language="lat")
cltk_nlp.pipeline.processes = [
    cltk.alphabet.processes.LatinNormalizeProcess,
    cltk.dependency.processes.LatinStanzaProcess
]


def preprocess(file_metadata: dict,
               save_dir: Path,
               tool_dir: Path):
    
    text_fpath, save_dir = Path(file_metadata['txt_fpath']), Path(save_dir)
    name = file_metadata['title']
    key = file_metadata['key']

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

            word_filter = [e for e, pos in enumerate(doc.pos) if pos != 'PUNCT']
            lemmata, new_lemmata, new_defs = [], [], []

            for i in word_filter:
                lemma = doc.lemmata[i]

                if not re.fullmatch(ALLOWED_LEMMATA, lemma) or lemma in BAD_LEMMATA:
                    continue

                lemmata.append(lemma)
                
                _k = lemma
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
                    
                    www_meaning = meanings(doc.tokens[i], tool_dir=tool_dir)
                    new_lemmata.append(lemma)
                    new_defs.append(www_meaning)
            
            r.lemmata_arr.extend(new_lemmata)
            r.lat_embeddings.extend([
                replace_if_none(lat_model.get_word_vector(w), lat_none) for w in new_lemmata
            ])
            r.definitions.extend(new_defs)
            r.eng_embeddings.extend(eng_model.encode(new_defs))
            c.lemmatised += ' '.join(lemmata) + '\n'

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
        
        # Final word2vec pass
        model = train_word2vec_model(
            corpus_path=save_dir / key / 'lemmatised.txt'
        )
        model.save(str(save_dir / key / 'word2vec.model'))

        return model
    
    with open(text_fpath, 'r', encoding='utf-8') as f:
        corpus = f.read()
    
    run_pipeline(corpus.split(CHUNK_SEP))

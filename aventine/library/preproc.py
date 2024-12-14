import re
import numpy as np
from tqdm import tqdm
from pathlib import Path

from cltk import NLP

from config import ROOT_FINGERPRINT, CORPUS_FINGERPRINT
from config import ALLOWED_LEMMATA, WWW_EXPR
from config import SENTENCE_TRANSFORMER_MODEL as ENG_MODEL
from utils import Checkpointer
from utils import senses


def preprocess(text_fpath: Path,
               save_dir: Path,
               key: str,
               title: str = None,
               english_embeddings: bool = True,
               tool_dir: Path = None,
               eng_model: str = ENG_MODEL):
    
    if english_embeddings:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(eng_model, trust_remote_code=True)
    
    text_fpath, save_dir = Path(text_fpath), Path(save_dir)
    
    cltk_nlp = NLP(language="lat")
    cltk_nlp.pipeline.processes.pop(-1)     # get rid of lexicon

    name = title if title is not None else key

    def run_pipeline(chunks):
        root_ckpt = Checkpointer(save_dir / 'root', ROOT_FINGERPRINT)
        corpus_ckpt = Checkpointer(save_dir / key, CORPUS_FINGERPRINT)
        c = corpus_ckpt.load()
        r = root_ckpt.load()

        if not c.meta:
            c.meta = {'completed': -1, 'total': len(chunks)}
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
            filter, new_lemmata = [], []
            for i in word_filter:
                lemma, pos = doc.lemmata[i], doc.pos[i]
                if not re.fullmatch(ALLOWED_LEMMATA, lemma):
                    continue
                _k = f'{lemma} ({pos})'
                if _k in r.existing_lemmata:
                    if key not in r.root_lemmata_info[_k]['texts']:
                        r.root_lemmata_info[_k]['texts'].add(key)
                        c.corpus_lemmata_info[_k] = {'count': 1, 'loc': [i]}
                    else:
                        c.corpus_lemmata_info[_k]['count'] += 1
                        c.corpus_lemmata_info[_k]['loc'].append(i)
                else:
                    filter.append(i)
                    new_lemmata.append(lemma)
                    r.existing_lemmata.add(_k)
                    r.root_lemmata_info[_k] = {'texts': {key}}
                    c.corpus_lemmata_info[_k] = {'count': 1, 'loc': [i]}

            r.lemmata_arr.extend(new_lemmata)
            r.lat_embeddings.extend(np.array(doc.embeddings)[filter])

            if english_embeddings:
                pbar = tqdm(new_lemmata, leave=False)
                new_definitions = []
                for lemma in pbar:
                    pbar.set_description(lemma)
                    new_definitions.append(senses(lemma, tool_dir, expr=WWW_EXPR))
                
                sents = model.encode(new_definitions)
                r.definitions.extend(new_definitions)
                r.eng_embeddings.extend(sents)
        
            c.meta['completed'] = chunk_index
            root_ckpt.save(r)
            corpus_ckpt.save(c)
    
    with open(text_fpath, 'r', encoding='utf-8') as f:
        corpus = f.read()
    
    run_pipeline(corpus.split('\n'))

preprocess('../data/sources/ecnmhwzfxqbbktcfubxy.txt',
           '../data/dump',
           'ecnmhwzfxqbbktcfubxy',
           title='naturalis historia',
           tool_dir='../tools/bin')

import logging
print('Importing libraries. This may take a while (~1 minute)...')

import os
import re
import json
import warnings
import numpy as np
from pathlib import Path
from typing import Union, List, Dict, Any, Tuple

import cltk
from cltk import NLP
from gensim.models import Word2Vec
from sentence_transformers import SentenceTransformer

from aventine.library.params import ROOT_FINGERPRINT, CORPUS_FINGERPRINT
from aventine.library.params import ALLOWED_SYMBOLS, ALLOWED_PUNCTS
from aventine.library.params import ALLOWED_LEMMATA, BAD_LEMMATA
from aventine.library.params_ml import SENTENCE_TRANSFORMER_MODEL as ENG_MODEL
from aventine.library.params_ml import WORD_EMBEDDING_MODEL as LAT_MODEL
from aventine.library.utils import Checkpointer
from aventine.library.utils import meanings
from aventine.library.utils import normalise_text
from aventine.library.files import perseus_url
from aventine.library.utils import get_null
from aventine.library.utils import clock_title


def get_metadata(
    metadata_dir: Path,
    text_id: str
) -> Dict[str, Any]:
    with open(
        metadata_dir/f'{text_id}.json',
        'r',
        encoding='utf-8'
    ) as f:
        return json.load(f)

def get_similarities(a, vects):
    sims = vects @ a.transpose()
    norm_a = np.linalg.norm(a)
    norm_v = np.linalg.norm(vects, axis=1)
    revalued = sims / (2 * norm_a * norm_v) + 0.5
    return revalued

def argmaxk(arr, k):
    return np.flip(np.argsort(arr)[-k:])

def atomise(cltk_nlp, query):
    query = re.sub(ALLOWED_PUNCTS, '', query)
    query = normalise_text(query, ALLOWED_SYMBOLS, ALLOWED_PUNCTS)
    cltk_nlp(text=query)
    atoms = [w.strip() for w in query.split(' ')
             if re.fullmatch(ALLOWED_LEMMATA, w) and w not in BAD_LEMMATA]
    return atoms


class Word2VecWrapper():
    def __init__(self, model):
        self.model = model
    
    def get_word_vector(self, word):
        try:
            return self.model.wv[word]
        except KeyError:
            return None


class AventineSearch():
    @clock_title('Aventine search engine initialisation')
    def __init__(
        self,
        sources_dir: str,
        index_dir: str,
        tool_dir: str,
        verbose: bool = True
    ) -> None:

        self.verbose = verbose
        vprint = lambda x: print(x) if verbose else None

        if not os.path.exists(sources_dir):
            return None

        self.sources_dir = Path(sources_dir)
        self.index_dir = Path(index_dir)
        self.tool_dir = Path(tool_dir)
        self.metadata_dir = self.sources_dir / 'metadata'

        vprint('Loading indexed data. This may take a while (~2 minutes)...')
        vprint('|- Loading metadata...')
        self.all_docs = [i for i in os.listdir(self.index_dir) if i != 'root']
        self.text_metas = {
            text_id: get_metadata(self.metadata_dir, text_id)
            for text_id in self.all_docs
        }
        self.id2title = {
            text_id: get_metadata(self.metadata_dir, text_id)['title']
            for text_id in self.all_docs
        }
        
        vprint('|- Loading checkpoints...')
        root_ckpt = Checkpointer(self.index_dir/'root', ROOT_FINGERPRINT)
        self.r = root_ckpt.load()
        self.text_ckpts = {
            text_id: Checkpointer(self.index_dir/text_id, CORPUS_FINGERPRINT).load()
            for text_id in self.all_docs
        }

        vprint('|- Creating quick access aliases...')
        self.root_lat_embeddings = np.array(self.r.lat_embeddings, copy=False)
        self.root_eng_embeddings = np.array(self.r.eng_embeddings, copy=False)
        self.root_lemmata_arr = np.array(self.r.lemmata_arr, copy=False)
        self.root_definitions = np.array(self.r.definitions, copy=False)
        
        vprint('|- Instantiating embedding models (takes a while)...')
        self.lat_model =  LAT_MODEL('lat')
        self.eng_model = SentenceTransformer(ENG_MODEL, trust_remote_code=True)
        self.lat_none, _ = get_null(self.lat_model, self.eng_model)

        vprint('|- Instantiating cltk pipelines...')
        self.cltk_nlp = NLP(language="lat")
        self.cltk_nlp.pipeline.processes = [
            cltk.alphabet.processes.LatinNormalizeProcess,
            cltk.dependency.processes.LatinStanzaProcess
        ]

        vprint('\n[ENGINE READY]')
    
    def _search(
        self,
        query: str,
        language: Union["eng", "lat"],
        texts: list = None,
        results: int = 50,
        scope: Union["universal", "root", str] = "universal"
    ) -> Dict:
        
        if query == '' or language not in {'eng', 'lat'}:
            warnings.warn("Invalid query or language.")
            return None
        
        if texts is None:
            texts = self.all_docs
        
        texts = set(texts)
        
        if language == 'eng':
            sent = self.eng_model.encode(query)
            sims = get_similarities(sent, self.root_eng_embeddings)
            lemmata = self.root_lemmata_arr
            repeated = set([query])
        
        elif language == 'lat':
            if scope == 'universal':
                embedder = self.lat_model
                lemmata = self.root_lemmata_arr
                vects = self.root_lat_embeddings
            else:
                wv_model = Word2Vec.load(str(self.index_dir/scope/'word2vec.model'))
                embedder = Word2VecWrapper(wv_model)
                lemmata, vects = [], []
                for k in wv_model.wv.key_to_index:
                    lemmata.append(k)
                    vects.append(wv_model.wv[k])
                lemmata, vects = np.array(lemmata, copy=False), np.array(vects, copy=False)
            
            senses = []
            atoms = atomise(self.cltk_nlp, query)
            repeated = set(atoms)
            for w in atoms:
                arr = embedder.get_word_vector(w)
                if arr is not None:
                    senses.append(arr)
            if len(senses) == 0:
                warnings.warn("No valid lemmata found in the query.")
                return None
            
            sent = np.mean(senses, axis=0)
            sims = get_similarities(sent, vects)

        # Given arbitrary arrays `lemma` and `sims`
        idx = 0
        found = 0
        data = []
        sorted = np.flip(np.argsort(sims))
        
        while found < results and idx < len(sorted):
            lemma_idx = sorted[idx]
            lemma = lemmata[lemma_idx]
            if lemma in self.r.existing_lemmata:
                meaning = self.root_definitions[lemma_idx]
            else:
                meaning = meanings(lemma, tool_dir=self.tool_dir)

            if (language == 'eng' and meaning in repeated) or \
               (language == 'lat' and lemma in repeated):
                idx += 1
                continue

            if len(texts) == 0:
                data.append({
                    'score': float(sims[lemma_idx]),
                    'lemma': lemma,
                    'definition': meaning,
                    'texts': [],
                    'links': {}
                })
                idx += 1
                found += 1

            elif lemma in self.r.existing_lemmata:
                intersect = self.r.root_lemmata_info[lemma]['texts'].intersection(texts)
                if intersect:
                    urls = {}
                    for text_id in intersect:
                        quotes = self.text_ckpts[text_id].corpus_lemmata_info[lemma]['loc']
                        urls[text_id] = [(perseus_url(self.text_metas[text_id],
                                                      self.text_metas[text_id]['index'][quote_id]),
                                          self.text_metas[text_id]['index'][quote_id])
                                         for quote_id in quotes]
                    data.append({
                        'score': float(sims[lemma_idx]),
                        'lemma': lemma,
                        'definition': self.root_definitions[lemma_idx],
                        'texts': list(intersect),
                        'links': urls
                    })
                    found += 1
            
            idx += 1

        return data
    
    @clock_title('Aventine search engine query')
    def search(self, *args, **kwargs):
        try:
            return self._search(*args, **kwargs)
        except:
            return None

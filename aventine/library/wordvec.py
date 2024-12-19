import os
from typing import Union

from gensim.models import Word2Vec

from aventine.library.config import WORD2VEC_EPOCHS, WORD2VEC_DIMS


class Corpus:
    def __init__(self, path):
        self.path = path

    def __iter__(self):
        with open(self.path, 'r', encoding='utf-8') as f:
            text = f.read().strip()
        for line in text.split('\n'):
            yield line.split(' ')


class MultiCorpus:
    def __init__(self, parent_dir):
        self.parent_dir = parent_dir

    def __iter__(self):
        for text_id in os.listdir(self.parent_dir):
            if text_id != 'root':
                fpath = os.path.join(self.parent_dir, text_id, 'lemmatised.txt')
                with open(fpath, 'r', encoding='utf-8') as f:
                    text = f.read().strip()
                for line in text.split('\n'):
                    yield line.split(' ')


def train_word2vec_model(
        corpus: Union[str, Corpus, MultiCorpus],
        window: int = 5,
        min_count: int = 1,
        workers: int = 4,
        vector_size: int = WORD2VEC_DIMS,
        epochs: int = WORD2VEC_EPOCHS
    ):
    model = Word2Vec(sentences=corpus,
                     vector_size=vector_size,
                     window=window,
                     min_count=min_count,
                     workers=workers)
    model.train(corpus, total_examples=model.corpus_count, epochs=epochs)

    return model

import os
import re
import json
import time
import random
import subprocess
import pickle as pkl
from pathlib import Path


def randkey(existing=[], length=20):
    while (key := ''.join([chr(random.randint(97, 122)) for _ in range(length)])) in existing:
        pass
    return key


def strfseconds(duration):
    trunc = int(duration)
    return f"{trunc//3600:02d}:{(trunc%3600)//60:02d}:{trunc%60:02d}.{int((duration-trunc)*1000)}"

def _clock_analysis(start, end, name=None):
    signature = strfseconds(end - start)
    
    if name is None:
        print(f"Process ran in time {signature}")
    else:
        print(f"Process `{name}` ran in time {signature}")

def clock(func):
    def decor(*args, **kwargs):
        start = time.time()
        ret = func(*args, **kwargs)
        end = time.time()
        _clock_analysis(start, end)
        return ret
    return decor

def clock_title(name):
    def wrapper(func):
        def decor(*args, **kwargs):
            start = time.time()
            ret = func(*args, **kwargs)
            end = time.time()
            _clock_analysis(start, end, name=name)
            return ret
        return decor
    return wrapper


def odds(arr):
    return [2*i+1 for i in range(len(arr)//2)]

def senses(word, tool_dir, expr=r"[a-zA-Z1-9,./;()\[\]\s]+\n([a-zA-Z1-9,./();\s]+)"):
    process = subprocess.Popen(["meanings", word],
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                shell=True,
                                text=True,
                                cwd=tool_dir)
    process.stdin.write(os.linesep * 5)
    process.stdin.flush()
    output = process.stdout.read().strip()
    
    lines = output.split('\n')

    matches = re.findall(word+expr, output)

    if len(matches) != 0:
        return ' '.join([m.strip() for m in matches])

    odd_lines = []

    for i in range(len(lines)//2):
        if (line := lines[2*i+1].strip()):
            odd_lines.append(line)

    return ' '.join(odd_lines)


class Bundler():
    def __init__(self):
        pass


class LargeDict(dict):
    def __init_subclass__(cls, **kwargs):
        return super().__init_subclass__(**kwargs)


def safely(save_func):
    def wrapper(obj, fpath: Path):
        _tmp_fpath = fpath.with_suffix('.tmp')
        ret = save_func(obj, _tmp_fpath)
        if os.path.exists(fpath):
            os.remove(fpath)
        os.rename(_tmp_fpath, fpath)
        return ret
    return wrapper

def carefully(load_func):
    def wrapper(fpath: Path):
        _tmp_fpath = fpath.with_suffix('.tmp')
        if os.path.exists(_tmp_fpath):
            raise FileExistsError(
                f'{_tmp_fpath} exists, the last checkpoint may have been corrupted during saving.'
            )
        obj = load_func(fpath)
        return obj
    return wrapper

@safely
def pickle_dump(obj, fpath: Path):
    with open(fpath, 'wb') as f:
        pkl.dump(obj, f)

@safely
def json_dump(obj, fpath: Path):
    with open(fpath, 'w', encoding='utf-8') as f:
        json.dump(obj, f, indent=4)

@carefully
def pickle_load(fpath):
    with open(fpath, 'rb') as f:
        return pkl.load(f)

@carefully
def json_load(fpath):
    with open(fpath, 'r', encoding='utf-8') as f:
        return json.load(f)


class Checkpointer():
    save_formats: dict = {
        None: (pickle_dump, 'pkl'),
        set: (pickle_dump, 'set.pkl'),
        list: (pickle_dump, 'pkl'),
        LargeDict: (pickle_dump, 'pkl'),
        dict: (json_dump, 'json')
    }
    load_formats: dict = {
        None: (pickle_load, 'pkl'),
        set: (pickle_load, 'set.pkl'),
        list: (pickle_load, 'pkl'),
        LargeDict: (pickle_load, 'pkl'),
        dict: (json_load, 'json')
    }

    def __init__(self,
                 dir: Path,
                 fingerprint: dict[str, type]):
        self.save_dir = Path(dir)
        self.fingerprint = fingerprint
        self.invar = {
            prop: self.fingerprint[prop]()
            for prop in self.fingerprint
        }
    
    def save(self, bundle, overwrite=True):
        os.makedirs(self.save_dir, exist_ok=True)
        for prop in self.fingerprint:
            obj = getattr(bundle, prop)
            if obj == self.invar[prop]:
                continue
            
            _t = type(obj) if type(obj) in self.save_formats else None
            save_func, file_ext = self.save_formats[_t]
            fpath = self.save_dir / f'{prop}.{file_ext}'

            if overwrite or not os.path.exists(fpath):
                save_func(obj, fpath)

    def load(self, overwrite=False):
        bundle = Bundler()
        for prop in self.fingerprint:
            _t = self.fingerprint[prop] if self.fingerprint[prop] in self.load_formats else None
            load_func, file_ext = self.load_formats[_t]
            fpath = self.save_dir / f'{prop}.{file_ext}'

            if overwrite or not os.path.exists(fpath):
                setattr(bundle, prop, _t())
            else:
                obj = load_func(fpath)
                setattr(bundle, prop, obj)
        
        return bundle

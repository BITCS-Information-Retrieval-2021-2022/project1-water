import json
import os

def save_ckpt(url,wordlist,wordlist_tmp,filepath):
    data = [
        {'url':url,
        'word':wordlist,
         'word_tmp':wordlist_tmp
         }
    ]

    with open(filepath,'w+') as f:
        json.dump(data,f)


def load_ckpt(filepath):
    with open(filepath,'r') as f:
        data = json.load(f)
    data = data[0]
    return data['url'],data['word'],data['word_tmp']
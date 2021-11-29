import json
import re


def save_ckpt(url, wordlist, wordlist_tmp, filepath):
    data = [
        {'url': url,
         'word': wordlist,
         'word_tmp': wordlist_tmp
         }
    ]

    with open(filepath, 'w+') as f:
        json.dump(data, f)


def load_ckpt(filepath):
    with open(filepath, 'r') as f:
        data = json.load(f)
    data = data[0]
    return data['url'], data['word'], data['word_tmp']


def has_attr(obj, attr):
    try:
        obj[attr]
        return True
    except KeyError:
        return False


def get_filename(filename, suffix):
    file_name = re.sub(r'Session\s*\w+\s*-\s*', '', filename)
    file_name = re.sub(r'SIGIR\s*\w*\s*-\s*', '', file_name)
    file_name = re.sub(r'\[[\x00-\x7F]+]\s*', '', file_name)  # 去掉中括号
    file_name = re.sub(r'(\([\x00-\x7F]*\))', '', file_name)  # 去掉小括号
    file_name = file_name.strip()
    file_name = re.sub(r'[\s\-]+', '_', file_name)  # 空格和连接符转化为_
    file_name = re.sub(r'_*\W', '', file_name)  # 去掉所有奇怪的字符
    return file_name + suffix


def set_checkpoint(filepath, args, mode='w+'):
    if not (isinstance(args, dict) and isinstance(mode, str)):
        return False

    with open(filepath, mode) as f:
        json.dump(args, f)
    return True


def load_checkpoint(filepath):
    with open(filepath, 'r') as f:
        data = json.load(f)
    return data

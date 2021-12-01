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


def get_month(mon):
    month_dict = {
        'January': '01',
        'Jan': '01',
        'February': '02',
        'Feb': '02',
        'March': '03',
        'Mar': '03',
        'April': '04',
        'Apr': '04',
        'May': '05',
        'June': '06',
        'Jun': '06',
        'July': '07',
        'Jul': '07',
        'August': '08',
        'Aug': '08',
        'September': '09',
        'Sept': '09',
        'October': '10',
        'Oct': '10',
        'November': '11',
        'Nov': '11',
        'December': '12',
        'Dec': '12'
    }
    return month_dict[mon.replace('.', '')]


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

def get_printable_text(str):
    return get_filename(str, '')

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

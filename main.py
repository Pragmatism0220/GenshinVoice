import json
import re
import pypinyin
from random import randint
from pydub import AudioSegment
from pathlib import Path
from tqdm import tqdm


def pinyin(word):
    return ''.join([''.join(i) for i in pypinyin.pinyin(word, style=pypinyin.NORMAL)]).strip()


def classify(in_f, out_f):
    song = AudioSegment.from_file(in_f)
    song = song.set_sample_width(2)  # 16-bit
    song = song.set_channels(1)
    song = song.set_frame_rate(22050)
    song.export(out_f, format='wav')


def convert(audio_filedict: dict, train_audio_path: str):
    train_audio_path = Path(train_audio_path)
    train_audio_path.mkdir(exist_ok=True)

    for npc_name, npc_audioinfo in audio_filedict.items():
        npc_train_audio_path = train_audio_path.joinpath(pinyin(npc_name))  # convert to pinyin to avoid Chinese path
        npc_train_audio_path.mkdir(exist_ok=True)
        npc_filelists = npc_train_audio_path.joinpath('filelists')
        npc_filelists.mkdir(exist_ok=True)

        with tqdm(total=len(npc_audioinfo), desc='converting %s...' % npc_name) as pbar:
            for file, text in npc_audioinfo:
                if file.endswith('.wav'):
                    file = Path(file)
                    new_audio_file = npc_train_audio_path.joinpath(file.name).resolve()
                    classify(file, new_audio_file)
                    if randint(1, 100) % 25 == 1:  # val
                        with open(npc_filelists.joinpath('val_filelist.txt'), 'a', encoding='utf8') as f_val:
                            f_val.write(new_audio_file.as_posix() + '|' + text + '\n')
                    else:  # train
                        with open(npc_filelists.joinpath('train_filelist.txt'), 'a', encoding='utf8') as f_train:
                            f_train.write(new_audio_file.as_posix() + '|' + text + '\n')
                pbar.update(1)


def get_audio_filedict(npc_names: set[str], json_dict: str = 'result.json'):
    audio_filedict = {npc_name: [] for npc_name in npc_names}

    current_path = Path(__file__).resolve().parent
    with open(json_dict, 'r', encoding='utf8') as f_dict:
        audio_dict = json.load(f_dict)
    with tqdm(total=len(audio_dict), desc='detecting...') as pbar:
        for val in audio_dict.values():
            try:
                if val['npcName'] in npc_names:
                    audio_path = current_path.joinpath(*val["fileName"].split('\\')).with_suffix('.wav').resolve()
                    if audio_path.is_file() and val['language'] == 'CHS' and val['type'] != 'Card':
                        audio_filedict[val['npcName']].append((audio_path.as_posix(),
                                                               re.sub(r'{.*}', '', re.sub(r'<.*?>', '', val['text']),
                                                                      flags=re.MULTILINE).replace('\\n', '').replace(
                                                                   '#', '')))
            except KeyError:
                pass
            pbar.update(1)
    return audio_filedict


if __name__ == '__main__':
    audio_dict_ = get_audio_filedict(
        npc_names={
            '派蒙', '流浪者', '珐露珊', '莱依拉', '纳西妲', '妮露', '坎蒂丝', '赛诺', '多莉', '提纳里', '柯莱',
            '鹿野院平藏', '久岐忍', '夜兰', '空', '荧', '神里绫人', '八重神子', '云堇', '申鹤', '荒泷一斗',
            '五郎', '优菈', '阿贝多', '托马', '胡桃', '达达利亚', '雷电将军', '珊瑚宫心海', '埃洛伊', '宵宫',
            '神里绫华', '枫原万叶', '温迪', '刻晴', '莫娜', '可莉', '琴', '迪卢克', '七七', '魈', '钟离', '甘雨',
            '早柚', '九条裟罗', '凝光', '菲谢尔', '班尼特', '丽莎', '行秋', '迪奥娜', '安柏', '重云', '雷泽',
            '芭芭拉', '罗莎莉亚', '香菱', '凯亚', '北斗', '诺艾尔', '砂糖', '辛焱', '烟绯'
        },
        json_dict='result.json',
    )
    convert(audio_filedict=audio_dict_, train_audio_path='./train_audio')

from scipy.io.wavfile import write
from mel_processing import spectrogram_torch
from text import text_to_sequence, _clean_text
from models import SynthesizerTrn
import utils
import commons
import sys
import re
from torch import no_grad, LongTensor
import logging
from winsound import PlaySound
from openai import OpenAI

chinese_model_path = ".\model\CN\model.pth"
chinese_config_path = ".\model\CN\config.json"
japanese_model_path = ".\model\H_excluded.pth"
japanese_config_path = ".\model\config.json"


modelmessage = """ID      Output Language
0       Chinese
1       Japanese
"""

idmessage_cn = """ID      Speaker
0       綾地寧々
1       在原七海
2       小茸
3       唐乐吟
"""

idmessage_jp = """ID      Speaker
0       綾地寧々
1       因幡めぐる
2       朝武芳乃
3       常陸茉子
4       ムラサメ
5       鞍馬小春
6       在原七海
"""

def get_input():
    # prompt for input
    print("You:")
    user_input = input()
    return user_input

def get_input_jp():
    # prompt for input
    print("You:")
    usr_in = input()
    if usr_in == 'quit()':
        return usr_in
    else:
        user_input = usr_in +" 使用日本语"
    return user_input

def get_token():
    token = input("Your API Key: \n")
    return token


logging.getLogger('numba').setLevel(logging.WARNING)

def ex_print(text, escape=False):
    if escape:
        print(text.encode('unicode_escape').decode())
    else:
        print(text)


def get_text(text, hps, cleaned=False):
    if cleaned:
        text_norm = text_to_sequence(text, hps.symbols, [])
    else:
        text_norm = text_to_sequence(text, hps.symbols, hps.data.text_cleaners)
    if hps.data.add_blank:
        text_norm = commons.intersperse(text_norm, 0)
    text_norm = LongTensor(text_norm)
    return text_norm


def ask_if_continue():
    while True:
        answer = input('Continue? (y/n): ')
        if answer == 'y':
            break
        elif answer == 'n':
            sys.exit(0)


def print_speakers(speakers, escape=False):
    if len(speakers) > 100:
        return
    print('ID\tSpeaker')
    for id, name in enumerate(speakers):
        ex_print(str(id) + '\t' + name, escape)


def get_speaker_id(message):
    speaker_id = input(message)
    if speaker_id == '':
        print(str(speaker_id) + ' is not a valid ID!')
        sys.exit(1)
    else:
        try:
            speaker_id = int(speaker_id)
        except:
            print(str(speaker_id) + ' is not a valid ID!')
            sys.exit(1)
    return speaker_id

def get_model_id(message):
    model_id = input(message)
    if model_id == '':
        print(str(model_id) + ' is not a valid ID!')
        sys.exit(1)
    else:
        try:
            model_id = int(model_id)
        except:
            print(str(model_id) + ' is not a valid ID!')
            sys.exit(1)
    return model_id

def get_label_value(text, label, default, warning_name='value'):
    value = re.search(rf'\[{label}=(.+?)\]', text)
    if value:
        try:
            text = re.sub(rf'\[{label}=(.+?)\]', '', text, 1)
            value = float(value.group(1))
        except:
            print(f'Invalid {warning_name}!')
            sys.exit(1)
    else:
        value = default
    return value, text


def get_label(text, label):
    if f'[{label}]' in text:
        return True, text.replace(f'[{label}]', '')
    else:
        return False, text
    
def get_reponse(input):
    msg = [
        {"role": "user", "content": input}
    ]

    # Call the OpenAI API with the prompt
    response = client.chat.completions.create(
      model="gpt-3.5-turbo",  # Adjust based on available engine versions
      messages=msg,
      temperature=0
    )
    # Extract and return the text from the API response
    return response.choices[0].message.content


def generateSound(inputString, id, model_id):
    if '--escape' in sys.argv:
        escape = True
    else:
        escape = False

    #model = input('0: Chinese')
    #config = input('Path of a config file: ')
    if model_id == 0:
        model = chinese_model_path
        config = chinese_config_path
    elif model_id == 1:
        model = japanese_model_path
        config = japanese_config_path
        

    hps_ms = utils.get_hparams_from_file(config)
    n_speakers = hps_ms.data.n_speakers if 'n_speakers' in hps_ms.data.keys() else 0
    n_symbols = len(hps_ms.symbols) if 'symbols' in hps_ms.keys() else 0
    emotion_embedding = hps_ms.data.emotion_embedding if 'emotion_embedding' in hps_ms.data.keys() else False

    net_g_ms = SynthesizerTrn(
        n_symbols,
        hps_ms.data.filter_length // 2 + 1,
        hps_ms.train.segment_size // hps_ms.data.hop_length,
        n_speakers=n_speakers,
        emotion_embedding=emotion_embedding,
        **hps_ms.model)
    _ = net_g_ms.eval()
    utils.load_checkpoint(model, net_g_ms)

    if n_symbols != 0:
        if not emotion_embedding:
            #while True:
            if(1 == 1):
                choice = 't'
                if choice == 't':
                    text = inputString
                    if text == '[ADVANCED]':
                        text = "我不会说"

                    length_scale, text = get_label_value(
                        text, 'LENGTH', 1, 'length scale')
                    noise_scale, text = get_label_value(
                        text, 'NOISE', 0.667, 'noise scale')
                    noise_scale_w, text = get_label_value(
                        text, 'NOISEW', 0.8, 'deviation of noise')
                    cleaned, text = get_label(text, 'CLEANED')

                    stn_tst = get_text(text, hps_ms, cleaned=cleaned)
                    
                    speaker_id = id 
                    out_path = "output.wav"

                    with no_grad():
                        x_tst = stn_tst.unsqueeze(0)
                        x_tst_lengths = LongTensor([stn_tst.size(0)])
                        sid = LongTensor([speaker_id])
                        audio = net_g_ms.infer(x_tst, x_tst_lengths, sid=sid, noise_scale=noise_scale,
                                               noise_scale_w=noise_scale_w, length_scale=length_scale)[0][0, 0].data.cpu().float().numpy()

                write(out_path, hps_ms.data.sampling_rate, audio)
if __name__ == "__main__":
    # Set OpenAI API key
    api_key = get_token()
    print()
    client = OpenAI(api_key=api_key, timeout=600)
    model_id = -1
    while True:
        print(modelmessage)
        model_id = int(get_model_id('选择回复语言: '))
        if model_id == 0 or model_id == 1:
            break
        else:
            print(str(model_id) + ' is not a valid ID!\n')
    print()

    speaker_id = -1
    while True:
        if model_id == 0:
            print("\n" + idmessage_cn)
        elif model_id == 1:
            print("\n" + idmessage_jp)
        
        speaker_id = get_speaker_id('选择角色: ')
        if (model_id == 0 and speaker_id in list(range(4))) or (model_id == 1 and speaker_id in list(range(7))):
            break
        else:
            print(str(speaker_id) + ' is not a valid ID!\n')
    print()

    while True:
        if model_id == 0:
            usr_in = get_input()

            if(usr_in == "quit()"):
                break
            resp = get_reponse(usr_in)
            print("ChatGPT:")
            answer = resp.replace('\n','')
            generateSound("[ZH]"+answer+"[ZH]", speaker_id, model_id)
            print(answer)
            PlaySound(r'./output.wav', flags=1)
        elif model_id == 1:
            usr_in = get_input_jp()
            if(usr_in == "quit()"):
                break
            resp = get_reponse(usr_in)
            print("ChatGPT:")
            answer = resp.replace('\n','')
            generateSound(answer, speaker_id, model_id)
            print(answer)
            PlaySound(r'./output.wav', flags=1)
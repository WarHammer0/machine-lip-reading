import numpy as np
import os
from align import read_align
from video import read_video
from sklearn.preprocessing import OneHotEncoder, LabelEncoder

# CURRENT_PATH = '/home/ubuntu/assignments/machine-lip-reading/preprocessing'
CURRENT_PATH = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = CURRENT_PATH + '/../data'
PREDICTOR_PATH = CURRENT_PATH + '/shape_predictor_68_face_landmarks.dat'


def text_to_labels(text):
    ret = []
    for char in text:
        if char >= 'a' and char <= 'z':
            ret.append(ord(char) - ord('a'))
        elif char == ' ':
            ret.append(26)
    return ret

def labels_to_text(labels):
# 26 is space, 27 is CTC blank char
    text = ''
    for c in labels:
        if c >= 0 and c < 26:
            text += chr(c + ord('a'))
        elif c == 26:
            text += ' '
    return text

def load_data(datapath, speaker, verbose=True, num_samples=1000, ctc_encoding=True):
    oh = OneHotEncoder()
    le = LabelEncoder()

    counter = 0
    done = False

    max_len = 0
    max_word_len = 0

    x = list()
    y = list()
    
    word_len_list = []
    input_len_list = []
    
    path = datapath + '/' + str(speaker)
    for root, dirs, files in os.walk(datapath):
        for name in files:
            if '.mpg' in name:
                if verbose is True:
                    print(str(counter) + ": reading - " + root + name)

                video = read_video(os.path.join(root, name), PREDICTOR_PATH)
                alignments = read_align(os.path.join(root, '../align/', name.split(".")[0] + ".align"))

                for start, stop, word in alignments:
                    if word == 'sil' or word == 'sp':
                        continue
                   
                    if (len(x) > 0):
                        _, d1, d2, d3 = video[start:stop].shape
                        _, prev_d1, prev_d2, prev_d3 = x[-1].shape
                        if (d1, d2, d3) != (prev_d1, prev_d2, prev_d3):
                            if verbose is True:
                                print("different size, skip")
                            continue
                    
                    x.append(video[start:stop])
                    y.append(word)
                            
                    max_word_len = max(max_word_len, len(word))
                    max_len = max(max_len, stop-start)

                    word_len_list.append(len(word))
                    input_len_list.append(stop-start)
                    
                    counter += 1
                    if counter % num_samples == 0:
                        
                        if not ctc_encoding:
                            y = le.fit_transform(y)
                            y = oh.fit_transform(y.reshape(-1, 1)).todense()

                        for i in range(len(x)):
                            result = np.zeros((max_len, 50, 100, 3))
                            result[:x[i].shape[0], :x[i].shape[1], :x[i].shape[2], :x[i].shape[3]] = x[i]
                            x[i] = result

                            if ctc_encoding:
                                res = np.ones(max_word_len) * -1
                                enc = np.array(text_to_labels(y[i]))
                                res[:enc.shape[0]] = enc
                                y[i] = res

                        if ctc_encoding:
                            y = np.stack(y, axis=0)

                        x = np.stack(x, axis=0)

                        print('saving numpy')
                        np.savez_compressed(speaker + '_x_' + str(counter / num_samples), x=x)
                        np.savez_compressed(speaker + '_y_' + str(counter / num_samples), y=y)
                        np.savez_compressed(speaker + '_wi_' + str(counter / num_samples),
                                            word_length=word_len_list, input_length=input_len_list)
                        
                        if counter == num_samples:
                            return counter / num_samples
                        
                        max_len = 0
                        max_word_len = 0

                        x = list()
                        y = list()

                        word_len_list = []
                        input_len_list = []
    
    
    if not ctc_encoding:
        y = le.fit_transform(y)
        y = oh.fit_transform(y.reshape(-1, 1)).todense()

    for i in range(len(x)):
        result = np.zeros((max_len, 50, 100, 3))
        result[:x[i].shape[0], :x[i].shape[1], :x[i].shape[2], :x[i].shape[3]] = x[i]
        x[i] = result

        if ctc_encoding:
            res = np.ones(max_word_len) * -1
            enc = np.array(text_to_labels(y[i]))
            res[:enc.shape[0]] = enc
            y[i] = res

    if ctc_encoding:
        y = np.stack(y, axis=0)

    x = np.stack(x, axis=0)

    print('saving numpy')
    np.savez_compressed(speaker + '_x_' + str(1 + counter / num_samples), x=x)
    np.savez_compressed(speaker + '_y_' + str(1 + counter / num_samples), y=y)
    np.savez_compressed(speaker + '_wi_' + str(1 + counter / num_samples),
                        word_length=word_len_list, input_length=input_len_list)
    
    
    return 1 + counter / num_samples

def read_data_for_speaker(speaker_id, count):
    x = np.load(speaker_id + "_x_" + str(count) + ".npz")['x']
    y = np.load(speaker_id + "_y_" + str(count) + ".npz")['y']
    word_len = np.load(speaker_id + "_wi_" + str(count) + ".npz")['word_length']
    input_len = np.load(speaker_id + "_wi_" + str(count) + ".npz")['input_length']
    return x, y, word_len, input_len


if __name__ == "__main__":
    load_data(DATA_PATH, 's1')


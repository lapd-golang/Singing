import os
import scipy.misc as sci
import numpy as np
from tqdm import tqdm
import musdb
import librosa
import random

def musdb2stft(save_dir='./data/', target='wo_drums'):
    """
    create stft dataset from MUSDB18
    :param save_dir: the path for the wanted data directory
    :param target: music target. for the original setup in the paper run twice, \
                   once for 'wo_vocals' and once for 'mixture'
    """
    mus = musdb.DB(root_dir='/home/moshe/ext/data/datasets/music/musdb18')
    tracks = mus.load_mus_tracks(subsets='train')
    save_dir = os.path.join(save_dir, target)
    if not os.path.exists(save_dir):
        print("Creating directory: {}".format(save_dir))
        os.makedirs(save_dir)

    for track in tqdm(tracks):

        music = switch_music(target, track)
        # resample audio file to 20480 Hz and create mono audio array from both channels
        music = music.mean(axis=1)
        samplerate = 20480
        music = librosa.resample(music, track.rate, samplerate)

        # parameters setting, resulting images of 257*256
        fft_size = 512
        hopsamp = fft_size // 8
        part_duration = 255 / (samplerate / hopsamp)
        length_song = music.shape[0]
        batch_size = round(samplerate * part_duration)
        counter = 1

        # data augmentation, taking 0.8 sec of audio from to create stft with different start time
        for shift_duration in tqdm([0, 0.3, 0.6]):
            shift_len = round(shift_duration * samplerate)
            number_of_parts = int(np.floor((length_song-shift_len) / batch_size))
            data = music[shift_len:number_of_parts*batch_size+shift_len]
            data2 = data.reshape(number_of_parts, int(data.size / number_of_parts))
            for row in data2:
                stft_full = librosa.core.stft(row, n_fft=fft_size, hop_length=hopsamp,
                                                      win_length=fft_size)
                stft_full = stft_full[0:-1, :]
                stft_mag = abs(stft_full)
                stft_mag = stft_mag ** 0.3
                songname = track.name + '_' + str(counter)
                songname = os.path.join(save_dir, songname)
                # if stft_mag.sum != 0:
                sci.imsave(songname + '.png', stft_mag)
                counter += 1


def divide_dataset(source_directory='./data/wo_vocals',
                   mixture_directory='./data/mixture',
                   dataset_name='vocals_dataset'):
    """
    create the dataset in a folder format to be used during train
    :param source_directory: path to observed component images (wo_vocals/wo_drums/wo_bass)
    :param mixture_directory: path to mixture images
    :param dataset_name: desired dataset name
    """
    main_dir = os.path.dirname(source_directory)
    save_dir = os.path.join(main_dir, dataset_name)
    test_names = ['testA', 'testB']
    train_names = ['trainA', 'trainB']
    origins = [source_directory, mixture_directory]
    print("Creating directory: {}".format(save_dir))
    os.makedirs(save_dir)
    for i, directory in enumerate(test_names):
        test_dir = os.path.join(save_dir, directory)
        os.makedirs(test_dir)
        files_names = os.listdir(origins[i])
        test_files = random.sample(files_names, round(0.05 * len(files_names)))
        for file in test_files:
            os.rename(os.path.join(origins[i], file), os.path.join(test_dir, file))
        os.rename(origins[i], os.path.join(save_dir, train_names[i]))


def switch_music(target, track):
    if target == 'wo_drums':
        music = track.targets['vocals'].audio
        music += track.targets['bass'].audio
        music += track.targets['other'].audio
    elif target == 'wo_vocals':
        music = track.targets['drums'].audio
        music += track.targets['bass'].audio
        music += track.targets['other'].audio
    elif target == 'wo_bass':
        music = track.targets['vocals'].audio
        music += track.targets['drums'].audio
        music += track.targets['other'].audio
    elif target == 'drums':
        music = track.targets['drums'].audio
    elif target == 'bass':
        music = track.targets['bass'].audio
    elif target == 'vocals':
        music = track.targets['vocals'].audio
    elif target == 'mixture':
        music = track.audio
        music = music * 0.5
    music = music * 2
    return music

if __name__ == '__main__':

    musdb2stft(save_dir='./data/datasets/lin_specs/musdb/', target='mixture')
    musdb2stft(save_dir='./data/datasets/lin_specs/musdb/', target='wo_vocals')
    divide_dataset()
    # divide_dataset(source_directory='../../data/datasets/lin_specs/musdb/wo_vocals',
    #                    mixture_directory='../../data/datasets/lin_specs/musdb/mixture',
    #                    methods_name='vocals_dataset')

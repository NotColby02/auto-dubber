import librosa 
import numpy as np 
import soundfile as sf 
import tensorflow as tf 
import tensorflow_hub as hub 

model = hub.load('https://tfhub.dev/google/yamnet/1')

def load_and_convert2mono(audio_file: str): 
    yamnet_sample_rate = 16000
    # Loads the audio_file at its native sample rate, in stereo 
    audio, sr = librosa.load(audio_file, sr=None, mono=False) 
    # Convert audio from stereo to mono 
    mono_audio = librosa.to_mono(audio) 
    # Resample the audio to 16000 Hz for YAMNet's preferred input reqs
    resampled_audio = librosa.resample(y=mono_audio, orig_sr=sr, target_sr=yamnet_sample_rate)
    return resampled_audio, yamnet_sample_rate

def get_audio_event_data(audio_file, window_size=1): 
    filepath = "./code/output.txt"
    resampled_audio, sample_rate = load_and_convert2mono(audio_file)

    # Making sure audio input is infact mono with a sample_rate of 16000 Hz 
    assert len(resampled_audio.shape) == 1, "Only mono audio is supported." 
    assert sample_rate == 16000, "Only 16,000 Hz sample rate is supported." 

    # Reshape audio data to expected input shape of YAMNNet 
    # input_batch = np.reshape(resampled_audio, (1, -1))
    
    # Run inference 
    scores, embeddings, spectrogram = model(resampled_audio) 
    scores = scores.numpy() 
    with open(filepath, "w") as file: 
        file.write(f"scores.shape: {scores.shape}\n\n")
    spectrogram = spectrogram.numpy() 

    with open("./code/yamnet_class_map.csv", 'r') as file: 
        next(file) 
        class_names = file.readlines() 

    # Internally, the model extracts "frames" from the audio signal and processes batches of these frames. 
    # This version of the model uses frames that are 0.96 second long and extracts one frame every 0.48 seconds 
    # Source: https://www.tensorflow.org/tutorials/audio/transfer_learning_audio
    frame_rate = 2.08 # (! Frame / .48 Secs)
    frames_per_window = int(frame_rate * window_size )

    with open(filepath, "a") as file: 
        for start in range(0, scores.shape[0], frames_per_window): 
            # Average score in selected window 
            end = min(start + frames_per_window, scores.shape[1])
            file.write(f"Start: {start} | End: {end}\n")
            avg_score = np.mean(scores[start:end, :], axis=0)
            # file.write(f"scores[start:end, :] - {scores[start:end, :]}\n")
            # file.write(f"avg_score: {avg_score}\n")

            # Find class with highest average score in selected window 
            class_id = np.argmax(avg_score) 
            file.write(f"class_id: {class_id}\n")
            class_name = class_names[class_id]
            file.write(f"class_name: {class_name}\n")
            class_score = avg_score[class_id]

            # Convert frame number to time 
            start_time = start * 0.48 
            end_time = start_time + window_size
            # start_time = start / frame_rate 
            # end_time = end / frame_rate 

            # Prints the dominant sound event for that window. 
            file.write(f"Time {start_time:.2f} to {end_time:.2f}: {class_name.strip()}\n\n")

        print("Audio event data captured")

get_audio_event_data("./audio/output_audio_2023-09-26.wav", window_size=1)

# mono_audio, sr = load_and_convert2mono("./audio/ManWhistleSoundEffect.wav")
# output_filepath = "./audio/audio_mono.wav"
# sf.write(output_filepath, mono_audio, 16000) 

# Issues: It can detect the when the crowd goes off, but it begins detecting speech a few seconds 
#         early. I guess that isn't terrible, just won't get the precise chops with the subtitles. 
#         HOWEVER, if you wanted to put the dub over this, then it would be an issue because it would
#         throw off the timing of when what was said.    
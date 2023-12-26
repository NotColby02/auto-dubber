import configparser
from datetime import datetime 
from moviepy.video.io.VideoFileClip import VideoFileClip
import os
from pydub import AudioSegment 

TODAYS_DATE = current_datetime = datetime.now().date()

def video_to_audio(video_file: str): 
    """
    Converts a given video file to audio, specifically to .wav format.
    
    The function will extract the audio from a given video file and save it
    to a .wav file in a directory named "audio". If the directory does not exist, 
    it will be created.

    Args:
        video_file (str): The path to the video file to be converted. This path 
        can be either absolute or relative.

    Returns:
        None. The function saves the output audio file in the "audio" directory.
    """
    print(f"video_to_audio(videio_file: {video_file})")
    os.makedirs("audio", exist_ok=True)
    audio_path = f"./audio/output_audio_{TODAYS_DATE}.wav" 

    video = VideoFileClip(video_file) 
    audio = video.audio 
    audio.write_audiofile(audio_path, codec="pcm_s16le") # Needed to convert to .wav fil
    print(f"video_to_audio[audio_path: {audio_path}])")
    return audio_path 

def break_audio_into_chunks(audio_path: str, max_secs: int, api_name: str): 
    """
    Breaks an audio file into chunks of 'max_secs' seconds each and exports them as .wav files.

    This function loads an audio file, segments it into 'max_secs' second intervals, and
    saves each segment as a .wav file in an "audio" directory. If the "audio" 
    directory does not exist, it will be created.

    Args:
        audio_path (str): The path to the audio file to be segmented. This path 
        can be either absolute or relative.

        max_secs (int): Represents the maximum amount of time the audio would have to broken down 
        in order to fit the restrictions of the API being called. 

    Returns:
        list of str: A list containing the file paths of the saved output audio chunks. Each element
        in the list corresponds to 'max_secs'-second chunk of the original audio file.
    """
    audio = AudioSegment.from_file(audio_path) 
    length_audio = len(audio)
    audio_chunks = []

    # Time in milliseconds 
    start_time = 0 
    end_time = max_secs * 1000

    i = 0 

    # Creating 60 sec chunks 
    while start_time < length_audio: 
        chunk = audio[start_time:end_time] 
        chunk_name = f"chunck{i}_{TODAYS_DATE}_{api_name}.wav"
        # Exporting chunk 
        chunk.export(f"./audio/{chunk_name}", format="wav") 
        audio_chunks.append(f"./audio/{chunk_name}")
        print(f"Processing chunk{i}. Start Time: {start_time/1000} secs.")
        start_time += (max_secs * 1000)
        end_time += (max_secs * 1000)
        i += 1
    return audio_chunks

def get_api_credentials(credential_path: str): 
    config = configparser.ConfigParser() 
    config.read(credential_path) 
    api_key = config['Credentials']['API_KEY']
    return api_key 
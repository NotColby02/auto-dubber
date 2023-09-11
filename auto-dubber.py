import configparser
from datetime import datetime, timedelta
from ibm_watson import SpeechToTextV1 
from ibm_watson.websocket import RecognizeCallback, AudioSource 
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from moviepy.video.io.VideoFileClip import VideoFileClip
import os 
from pydub import AudioSegment 
# import whisper 
# from whisper.utils import get_writer

TODAYS_DATE = current_datetime = datetime.now().date()
MAX_TIME = timedelta(hours=7, minutes=55, seconds=0)

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
    os.makedirs("audio", exist_ok=True)
    audio_path = f"audio/output_audio_{TODAYS_DATE}.wav" 

    video = VideoFileClip(video_file) 
    audio = video.audio 
    audio.write_audiofile(audio_path, codec="pcm_s16le") # Needed to convert to .wav file 

def break_audio_into_chunks(audio_path: str): 
    """
    Breaks an audio file into chunks of 60 seconds each and exports them as .wav files.

    This function loads an audio file, segments it into 60 second intervals, and
    saves each segment as a .wav file in an "audio" directory. If the "audio" 
    directory does not exist, it will be created.

    Args:
        audio_path (str): The path to the audio file to be segmented. This path 
        can be either absolute or relative.

    Returns:
        list of str: A list containing the file paths of the saved output audio chunks. Each element
        in the list corresponds to 60-second chunk of the original audio file.
    """
    audio = AudioSegment.from_file(audio_path) 
    length_audio = len(audio)
    audio_chunks = []

    # Time in milliseconds 
    start_time = 0 
    end_time = 60000

    i = 0 

    # Creating 60 sec chunks 
    while start_time < length_audio: 
        chunk = audio[start_time:end_time] 
        chunk_name = f"chunck{i}_{TODAYS_DATE}.wav"
        # Exporting chunk 
        chunk.export(f"audio/{chunk_name}", format="wav") 
        audio_chunks.append(f"audio/{chunk_name}")
        print(f"Processing chunk{i}. Start Time: {start_time/1000} secs.")
        start_time += 60000
        end_time += 60000
        i += 1
    return audio_chunks

def read_total_duration(): 
    """
    Reads the total duration from a text file and returns it as a timedelta object. 

    Returns:
        timedelta: A timedelta object representing the total duration read from the file,
        or a default duration of '00:00:00' if the file is missing or invalid.
    """
    try: 
        with open("total_duration.txt", "r") as file: 
            duration_str = file.read() 
            hours, minutes, seconds = map(int, duration_str.split(":"))
            print(f"duration_str: {duration_str}")
            return timedelta(hours=hours, minutes=minutes, seconds=seconds)
    except FileNotFoundError: 
        return timedelta(hours=0, minutes=0, seconds=0)
    
def update_total_duration(duration: timedelta): 
    """
    Updates the total duration in a text file with the provided duration.

    This function takes a timedelta object representing a duration and writes it to
    a file named 'total_duration.txt' in the format 'HH:MM:SS' (hours, minutes, seconds).

    Args:
        duration (timedelta): The duration to be written to the file.

    Returns:
        None
    """
    hours, remainder = divmod(duration.seconds, 3600) 
    minutes, seconds = divmod(remainder , 60)

    with open("total_duration.txt", "w") as file: 
        file.write(f"{hours:02}:{minutes:02}:{seconds:02}")

class TotalDurationExceeded(Exception): 
    """
    Exception raised when the total duration exceeds a specified limit.

    This exception is raised when the total duration of some process exceeds a predefined
    threshold. It provides a clear indication that the process has exceeded its allowable
    duration.
    """
    pass 



def main(): 
    # Getting Credentials 
    config = configparser.ConfigParser() 
    config.read("credentials.txt") 
    api_key = config['Credentials']['API_KEY']
    api_url = config['Credentials']['API_URL']
    print(f"api_key: {api_key}")
    print(f"api_url: {api_url}")

    # Setting up Authentication 
    authenticator = IAMAuthenticator(api_key) 
    speech_to_text = SpeechToTextV1(
        authenticator=authenticator
    )
    speech_to_text.set_service_url(api_url)

    # Stripping audio from video file:
    video_path = "video/bench-pr-gone-horribly-wrong.mp4"
    video_to_audio(video_path)

    # Breaking audio into 60 second chunks to fit IBM's free plan usage. 
    audio_chunks = break_audio_into_chunks(f"audio/output_audio_{TODAYS_DATE}.wav")
    print(f"audio_chunks: {audio_chunks}")

    # Before calling API, making sure we haven't transcribed more than 475 minutes 
    # worth of data so that we can still use the free tier
    total_duration = read_total_duration() 
    print(f"total_duration: {total_duration}")
    print(f"MAX_TIME: {MAX_TIME}")

    # Check if the total duration exceeds the threshold 
    if (total_duration >= MAX_TIME): 
        raise TotalDurationExceeded("Total duration exceeded 7 hours and 55 minutes. Stopping further processing.")

    # Processing audio chunks 
    for chunk_path in audio_chunks: 
        chunk_duration = len(AudioSegment.from_file(chunk_path)) / 1000 # in seconds 
        total_duration += timedelta(seconds=chunk_duration)

    update_total_duration(total_duration) 

    # Getting Transcriptions 
    with open(audio_chunks[0], "rb") as audio_file: 
        audio_source = AudioSource(audio_file)
        response = speech_to_text.recognize(
            audio=audio_source,
            content_type="audio/wav", 
            model="en-US_BroadbandModel"
        ).get_result() 

    # Print the transcription 
    for result in response["results"]: 
        print(result["alternatives"][0]["transcript"])

if __name__ == "__main__": 
    main()

# # Transcribing audio 
# # model = whisper.load_model("base")
# # print(audio_chunks[0])
# # result = model.transcribe(audio_chunks[0])
# # result1 = model.transcribe(audio_chunks[1])
# # print(result["text"])
# # # print((result["segments"][1]))

# # Using API to just get an SRT file of the transcription. 


# # # Saving as an SRT File https://wandb.ai/wandb_fc/gentle-intros/reports/OpenAI-Whisper-How-to-Transcribe-Your-Audio-to-Text-for-Free-with-SRTs-VTTs---VmlldzozNDczNTI0#what-is-an-srt/vtt-file?
# # # srt_writer = get_writer("srt", "./")
# # # srt_writer(result, audio_chunks[0])
# # # Have to use colab in order to get this to work. 
# # # Also transcription is not good depending on quality of the audio/how loud the speaker was. 
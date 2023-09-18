import audio_video_script as avs
import configparser
from datetime import datetime, timedelta
from ibm_watson import SpeechToTextV1 
from ibm_watson.websocket import RecognizeCallback, AudioSource 
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from moviepy.video.io.VideoFileClip import VideoFileClip
import os 
from pydub import AudioSegment 
import time 
import threading 
from tqdm import tqdm 
# import whisper 
# from whisper.utils import get_writer

TODAYS_DATE = current_datetime = datetime.now().date()
MAX_TIME = timedelta(hours=7, minutes=55, seconds=0)

def read_total_duration(): 
    """
    Reads the total duration from a text file and returns it as a timedelta object. 

    Returns:
        timedelta: A timedelta object representing the total duration read from the file,
        or a default duration of '00:00:00' if the file is missing or invalid.
    """
    try: 
        with open("total_duration_ibm.txt", "r") as file: 
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

    with open("total_duration_ibm.txt", "w") as file: 
        file.write(f"{hours:02}:{minutes:02}:{seconds:02}")

class TotalDurationExceeded(Exception): 
    """
    Exception raised when the total duration exceeds a specified limit.

    This exception is raised when the total duration of some process exceeds a predefined
    threshold. It provides a clear indication that the process has exceeded its allowable
    duration.
    """
    pass 

def write_transcription_from_ibm(response, video_name): 
    """
    Write transcriptions with metadata to a text file.

    This function takes an IBM Watson Speech to Text API response and a video name,
    and writes the transcriptions and associated metadata to a text file. The file
    is saved in a "transcriptions" directory within the repository.

    Args:
        response (dict): The IBM Watson Speech to Text API response containing transcription results.
        video_name (str): The name of the video for which the transcriptions are generated.

    Returns:
        None: The function writes the transcriptions to a file but does not return any value.

    Example usage:
        response = call_ibm_watson_speech_to_text()
        write_transcription_from_ibm(response, "example_video")
    """
    # Writing Transcriptions to repo. 
    os.makedirs("transcriptions", exist_ok=True) 
    file_name = f"{TODAYS_DATE}_{video_name}_transcription.txt"

    with open(f"transcriptions/{file_name}", "w") as transcription_file: 
        for result in response["results"]: 
            alternatives = result["alternatives"]
            for alternative in alternatives: 
                transcript = alternative["transcript"]
                confidence = alternative.get("confidence", None) 
                is_final = result.get("final", False) 

                # Write the transcription and the metadata to the file 
                transcription_file.write(f"Transcript: {transcript}\n")
                if confidence is not None: 
                    transcription_file.write(f"Confidence: {confidence}\n")
                transcription_file.write(f"Is Final: {is_final}\n")
                transcription_file.write("\n") # Separate entries with blank lines 

    print(f"Trancriptions with metadata written to: transcriptions/{file_name}")

def get_transcription_from_ibm(service, audio_chunks): 
    # Getting Transcriptions w/ IBM Watson-Pretty Bad  
    with open(audio_chunks[0], "rb") as audio_file: 
        response = service.recognize(
            audio=audio_file,
            content_type="audio/wav", 
            model="en-US_BroadbandModel"
        ).get_result() 

    return response 

def main(): 
    try: 
        # Getting Credentials 
        config = configparser.ConfigParser() 
        config.read("./credentials/ibm_credentials.txt") 
        api_key = config['Credentials']['API_KEY']
        api_url = config['Credentials']['API_URL']
        print(f"api_key: {api_key}")
        print(f"api_url: {api_url}")
    except KeyError as e: 
        print(f"Error: {e}. Check config file")

    # Setting up Authentication 
    authenticator = IAMAuthenticator(api_key) 
    speech_to_text = SpeechToTextV1(
        authenticator=authenticator
    )
    speech_to_text.set_service_url(api_url)

    # Stripping audio from video file:
    video_path = "./video/JeffTeague.mp4"
    avs.video_to_audio(video_path)

    # Breaking audio into 60 second chunks to fit IBM's free plan usage. 
    audio_chunks = avs.break_audio_into_chunks(f"./audio/output_audio_{TODAYS_DATE}.wav", 60)
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

    # Create a progress bar with unknown number of iterations 
    progress_bar = tqdm(desc="Transcribing audio", unit=" ms", dynamic_ncols=True)

    # Results to store transcription results 
    response = [] 

    # Start transcription thread  
    transcription_thread = threading.Thread(target=lambda: response.append(get_transcription_from_ibm(speech_to_text, audio_chunks)))

    # Starting threads 
    transcription_thread.start() 

    # Updating progress bar while bar is being fetched. 
    while transcription_thread.is_alive(): 
        time.sleep(0.1) 
        progress_bar.update(1)

    # Waiting for thread to close
    transcription_thread.join()
    progress_bar.close() 

    response = response[0]
    # Print the transcription 
    for result in response["results"]: 
        print(result["alternatives"][0]["transcript"])
    # Writing Transcriptions to repo.   
    write_transcription_from_ibm(response, "bench_pr_gone_horribly_wrong")

if __name__ == "__main__": 
    main()


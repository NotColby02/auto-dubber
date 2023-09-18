import audio_video_script as avs 
import os
import openai 

def update_request_limit():
    request_limit_tracker = "./code/rate_limits_openai.txt"
    requests_made_str = ""
    requests_made = 0 
    try: 
        with open(request_limit_tracker, "r") as file: 
            requests_made_str = file.read().strip()
    except FileNotFoundError: 
        print("File Not Found. Cannot update request limit") 

    requests_made = int(requests_made_str) + 1 
    
    with open(request_limit_tracker, "w") as file: 
        file.write(str(requests_made))

    return requests_made

def check_request_limit(requests_made: int): 
    return True if requests_made < 200 else False 

class AudioFileTooLong(Exception): 
    pass 

def transcribe_audio_whisperai(audio_file_path: str): 
    with open(audio_file_path, "rb") as audio_file: 
        transcription = openai.Audio.transcribe("whisper-1", audio_file) 
    return transcription

def main(): 
    API_KEY = avs.get_openai_credentials("./credentials/openai_credentials.txt")
    print(f"API_KEY: {API_KEY}")
    openai.api_key = API_KEY 
    MAX_MB_FOR_VIDEO = 25 
    video_file = "./video/CoachPrime.mp4"
    todays_date = avs.TODAYS_DATE

    requests_made_so_far = update_request_limit() 
    is_within_limits = check_request_limit(requests_made_so_far)
    
    if is_within_limits: 
        avs.video_to_audio(video_file) 
        audio_file = "./audio/output_audio_2023-09-12.wav"
        file_size = os.path.getsize(audio_file) / (1024 * 1024) 
        print(f"audio_file size: {file_size} MB")

        if file_size > MAX_MB_FOR_VIDEO: 
            print("File too large to transcribe.")
            raise AudioFileTooLong 
        
        transcription = transcribe_audio_whisperai(audio_file) 

    print("\n\n\n\n\n\n\n")
    print(transcription)
        



if __name__ == "__main__": 
    main() 
import audio_video_script as avs 
from datetime import datetime 
# import google.cloud.translate 
import elevenlabs 
from google.cloud import translate 
import openai 
import os

TODAYS_DATE = datetime.now().date() 
GOOGLES_MAX_TOKENS = 500000

def get_video_name(video_file: str): 
    video_name = video_file.split("/")[-1].split(".")[0]
    print(f"get_video_name[video_name: {video_name}]")
    return video_name 

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
    def __init__(self, message="File too large to transcribe. File size must be less than 25 MB"): 
        self.message = message 
        super().__init__(self.message) 

def transcribe_audio_whisperai(audio_file_path: str): 
    with open(audio_file_path, "rb") as audio_file: 
        transcription = openai.Audio.transcribe(model="whisper-1", file=audio_file, response_format="srt") 
    return transcription

def write_transcription_to_file(srt_transcription: str, video_name: str): 
    file_path = f"./transcriptions/{TODAYS_DATE}_{video_name}_transcription.srt"
    with open(file_path, "w") as file: 
        file.write(srt_transcription) 

    return file_path 

def turn_srt_file_to_paragraph(srt_file): 
    try: 
        with open(srt_file, "r", encoding="utf-8") as file: 
            lines = file.readlines() 
            
        paragraph = "" 
        is_subtitle_block = False 

        for line in lines: 
            line = line.strip() # Check for blank line 
            if not line:  
                continue 
            elif line.isdigit(): # Check if line number 
                continue 
            elif "-->" in line: # Check if time sequence 
                continue 
            else: # Subtitle line 
                paragraph += f"{line} | "
            
        return paragraph.strip()
    except FileNotFoundError: 
        return "SRT file not found."
    
def update_token_tracker(transcribed_paragraph: str):
    tokens_transcribed =  len(transcribed_paragraph)
    google_translate_api_tracker = "./token_tracker/google_translation_api.txt" 
    with open(google_translate_api_tracker, "r") as file: 
        tokens_transcribed_so_far = file.read().strip() 

    total_tokens_transcribed = int(tokens_transcribed_so_far) + tokens_transcribed 

    with open(google_translate_api_tracker, "w") as file: 
        file.write(str(total_tokens_transcribed)) 

    return total_tokens_transcribed

class GoogleTokenLimitReached(Exception): 
    def __init__(self, message="Google's Translate API has reached maxed token. Please try again later."): 
        self.message = message 
        super().__init__(self.message) 

def write_translation_to_file(translated_text: str, video_name: str): 
    file_path = f"./translated_text/{video_name}_translation.txt" 
    with open(file_path, 'w', encoding="utf-8") as file: 
        file.write(translated_text)

def google_translate_basic(text: str, target_language_code: str): 
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./credentials/autodubber-f5336cc011ff.json"
    from google.cloud import translate_v2 as translate 
    translate_client = translate.Client() 
    if isinstance(text, bytes): 
        text = text.decode("utf-8")
    result = translate_client.translate(text, target_language=target_language_code)
    translation = result["translatedText"]
    return translation  

def get_dubbed_audio(translated_text: str, video_name: str): 
    filename = f"./translated_audio/{video_name}.wav"
    elevenlabs_api_key = avs.get_api_credentials("./credentials/elevenlabs_creds.txt")
    elevenlabs.set_api_key(elevenlabs_api_key)
    audio = elevenlabs.generate(
        text=translated_text,
        voice="Ryan", # Need to changle later to allow user to pick voice
        model="eleven_multilingual_v2"
    )
    elevenlabs.save(audio=audio, filename=filename)
    
def main(): 
    API_KEY_OPENAI = avs.get_api_credentials("./credentials/openai_credentials.txt")
    print(f"API_KEY: {API_KEY_OPENAI}")
    openai.api_key = API_KEY_OPENAI 
    MAX_MB_FOR_VIDEO = 25 
    video_file = "./video/CoachPrime.mp4"
    video_name = get_video_name(video_file)
    print(f"main[video_name: {video_name}]")
    todays_date = avs.TODAYS_DATE

    requests_made_so_far = update_request_limit() 
    is_within_limits = check_request_limit(requests_made_so_far)
    
    if is_within_limits: 
        avs.video_to_audio(video_file) 
        audio_file = F"./audio/output_audio_{TODAYS_DATE}.wav"
        print(f"main[audio_file: {audio_file}]")
        file_size = os.path.getsize(audio_file) / (1024 * 1024) 
        print(f"audio_file size: {file_size} MB\n\n")

        if file_size > MAX_MB_FOR_VIDEO: 
            raise AudioFileTooLong 
        
        # transcription = "would transcribe here"
        transcription = transcribe_audio_whisperai(audio_file) 
        write_transcription_to_file(transcription, video_name) 
        srt_paragraph = turn_srt_file_to_paragraph("./transcriptions/2023-09-19_CoachPrime_transcription.srt")
        print(f"srt_paragraph: {srt_paragraph}\n\n") 

        total_tokens_transcribed = update_token_tracker(srt_paragraph)
        print(f"total_tokens_transcribed: {total_tokens_transcribed}\n\n")

        if total_tokens_transcribed >= GOOGLES_MAX_TOKENS: 
            raise GoogleTokenLimitReached  
        
        translation = google_translate_basic(srt_paragraph, "es-419") # es-419 translates to Latin American Spanish (Not Spain) 
        print(translation) 
        write_translation_to_file(translation, video_name) 

        get_dubbed_audio(translation, video_name)
        
if __name__ == "__main__": 
    main() 
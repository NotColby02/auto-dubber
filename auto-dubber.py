from moviepy.video.io.VideoFileClip import VideoFileClip
from pydub import AudioSegment 
import whisper 
from whisper.utils import get_writer
import os 

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
    audio_path = "audio/output_audio.wav" 

    video = VideoFileClip(video_file) 
    audio = video.audio 
    audio.write_audiofile(audio_path, codec="pcm_s16le") # Needed to convert to .wav file 

video_path = "video/bench-pr-gone-horribly-wrong.mp4"
video_to_audio(video_path)

# Whisper API (can be used offline) can only transcribe in 30 second chunks. 
# Seeing if I can break the audio into 30 second chunks, and then using Whisper to transcribe that. 
def break_audio_into_chunks(audio_path: str): 
    """
    Breaks an audio file into chunks of 30 seconds each and exports them as .wav files.

    This function loads an audio file, segments it into 30 second intervals, and
    saves each segment as a .wav file in an "audio" directory. If the "audio" 
    directory does not exist, it will be created.

    Args:
        audio_path (str): The path to the audio file to be segmented. This path 
        can be either absolute or relative.

    Returns:
        list of str: A list containing the file paths of the saved output audio chunks. Each element
        in the list corresponds to a 30-second chunk of the original audio file.
    """
    audio = AudioSegment.from_file(audio_path) 
    length_audio = len(audio)
    audio_chunks = []

    # Time in milliseconds 
    start_time = 0 
    end_time = 30000

    i = 0 

    # Creating 30 sec chunks 
    while start_time < length_audio: 
        chunk = audio[start_time:end_time] 
        chunk_name = f"chunck{i}.wav"
        # Exporting chunk 
        chunk.export(f"audio/{chunk_name}", format="wav") 
        audio_chunks.append(f"audio/{chunk_name}")
        print(f"Processing chunk{i}. Start Time: {start_time/1000} secs.")
        start_time += 30000
        end_time += 30000
        i += 1
    return audio_chunks


audio_chunks = break_audio_into_chunks("audio/output_audio.wav") 

# Transcribing audio 
model = whisper.load_model("base")
result = model.transcribe(audio_chunks[0])
result1 = model.transcribe(audio_chunks[1])
print(result["text"])
print((result["segments"][1]))

# Saving as an SRT File https://wandb.ai/wandb_fc/gentle-intros/reports/OpenAI-Whisper-How-to-Transcribe-Your-Audio-to-Text-for-Free-with-SRTs-VTTs---VmlldzozNDczNTI0#what-is-an-srt/vtt-file?
# srt_writer = get_writer("srt", "./")
# srt_writer(result, audio_chunks[0])
# Have to use colab in order to get this to work. 
# Also transcription is not good depending on quality of the audio/how loud the speaker was. 
from moviepy.video.io.VideoFileClip import VideoFileClip
import os 

video_path = "video/when-the-footlocker-employee-knows-your-a-sneaker-reseller.mp4"
os.makedirs("audio", exist_ok=True)
audio_path = "audio/output_audio.wav" 

video = VideoFileClip(video_path) 
audio = video.audio 
audio.write_audiofile(audio_path, codec="pcm_s16le") # Needed to convert to .wav file 



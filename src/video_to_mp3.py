# converts the videos into mp3

import os
import subprocess

files = os.listdir("data/videos")

for file in files:
    #print(file)
    tutorial_number = file.split(".")[0].split("#")[1]
    #print(tutorial_number)
    file_name = file.split("   ")[0]
    print(tutorial_number, file_name)
    subprocess.run(["ffmpeg", "-i", f"data/videos/{file}", f"data/audios/{tutorial_number}_{file_name}.mp3"])
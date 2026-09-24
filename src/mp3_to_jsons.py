

import whisper
import json
import os
from typing import Any, cast

model = whisper.load_model("large-v2")

audios = os.listdir("data/audios")

for audio in audios:
    #print(audio)
    if("_" in audio):
        number = audio.split("_")[0]
        title = audio.split("_")[1].split(".")[0]
        print(number, title)
        result = model.transcribe(audio=f"audios/{audio}",
        # result = model.transcribe(audio=f"audios/sample.mp3",
                                language="hi",
                                task="translate",
                                word_timestamps=False)
        
        chunks=[]
        for segment in result["segments"]:
            segment_data = cast(dict[str, Any], segment)
            chunks.append({"number": number, "title": title, "start": segment_data["start"], "end": segment_data["end"], "text": segment_data["text"]})
            
        chunks_with_metadata = {"chunks": chunks, "text": result["text"]}

        with open(f"data/jsons/{audio}.json", "w") as f:
            json.dump(chunks_with_metadata, f)
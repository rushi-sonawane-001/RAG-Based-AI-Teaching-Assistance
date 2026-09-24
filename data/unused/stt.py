#speech to text

import whisper
import json
from typing import Any, cast

model = whisper.load_model("large-v2")

result = model.transcribe(audio="audios/sample.mp3",
                          language="hi",
                          task="translate",
                          word_timestamps=False)

#print(result["segments"])

chunks=[]
for segment in result["segments"]:
    segment_data = cast(dict[str, Any], segment)
    chunks.append({"start": segment_data["start"], "end": segment_data["end"], "text": segment_data["text"]})
    
print(chunks)

with open("output.json", "w") as f:
    json.dump(chunks, f)
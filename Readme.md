# How to use this RAG AI Teaching Assistance on your Data

## Step-1: Collect your videos
Move all your video files to the videos folder

## Step-2: Convert to mp3
Convert all the video files to mp3 by running video_to_mp3

## Step-3: Convert mp3 to json
Convert all the mp3 files to json by running mp3_to_json

## Step-4: Convert the jsons files to Vectors
Use the file preprocess_jsons to convert the json file to a dataframe with Embeddings and save it as a joblib pickel

## Step-5: Prompt Generation and feeding to LLM
Read the joblib file and load it into the memory. then create a relevant prompt as per the user query and feed it to the LLM
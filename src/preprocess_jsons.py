import requests
import os
import json
import pandas as pd
import numpy as np
import joblib
from sklearn.metrics.pairwise import cosine_similarity

def create_embedding(text_list):
    r = requests.post(
        "http://localhost:11434/api/embed",
        json={
            "model": "bge-m3",
            "input": text_list
        },
        timeout=300
    )

    # print("Status Code:", r.status_code)

    # if r.status_code != 200:
    #     print("Ollama Error:")
    #     print(r.text)
    #     r.raise_for_status()

    data = r.json()

    # if "embeddings" not in data:
    #     raise Exception(
    #         f"Embedding not found. Ollama response: {data}"
    #     )

    return data["embeddings"]


jsons = os.listdir("data/newjsons")

my_dicts = []
chunk_id = 0

BATCH_SIZE = 200


for json_file in jsons:

    print(f"\nProcessing file: {json_file}")

    with open(f"data/newjsons/{json_file}", encoding="utf-8") as f:
        content = json.load(f)

    chunks = content["chunks"]

    print(f"Total chunks: {len(chunks)}")

    for start in range(0, len(chunks), BATCH_SIZE):

        batch = chunks[start:start + BATCH_SIZE]

        texts = [chunk["text"] for chunk in batch]

        # print(
        #     f"\nEmbedding chunks "
        #     f"{start} to {start + len(batch) - 1}"
        # )

        embeddings = create_embedding(texts)

        for i, chunk in enumerate(batch):

            chunk["chunk_id"] = chunk_id
            chunk["embedding"] = embeddings[i]
            chunk_id += 1
            my_dicts.append(chunk)

            # if(i == 5):   #read only 5 chunks
            #     break
        # break
   


# print("\n==============================")
# print(f"Total embeddings created: {len(my_dicts)}")
# print("==============================")
# print(my_dicts)

df = pd.DataFrame.from_records(my_dicts)
# print(df)
# save this dataframe
joblib.dump(df, "models/embeddings.joblib")


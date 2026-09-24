import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import joblib
import requests
import os
# from dotenv import load_dotenv
# from google import genai

# # Load environment variables from .env
# load_dotenv()

# # Get Gemini API key
# api_key = os.getenv("GEMINI_API_KEY")

# if not api_key:
#     raise ValueError("GEMINI_API_KEY not found. Check your .env file.")

# # Create Gemini client
# client = genai.Client(api_key=api_key)

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


def inference(prompt):
    r = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3.2",
            "prompt": prompt,
            "stream": False
        },
        timeout=300
    )

    print("Status Code:", r.status_code)
    print("Raw Response:", r.text)

    r.raise_for_status()

    response = r.json()

    return response


# def inference_gemini(prompt):
#     interaction = client.interactions.create(
#         model="gemini-3.8-flash",
#         input=prompt
#     )

#     return interaction.output_text


df = joblib.load('models/embeddings.joblib')

incoming_query = input("Ask a Question: ")
question_embedding = create_embedding([incoming_query])[0]
# print(question_embedding)

# find similarities of question_embeddings with other embediings
embedding_matrix = np.vstack(df['embedding'].values)

#print(embedding_matrix)
# print(embedding_matrix.shape)

similarities = cosine_similarity(
    embedding_matrix,
    [question_embedding]
).flatten()

# print(similarities)
top_results = 5
max_indx = similarities.argsort()[::-1][0:top_results]
# print(max_indx)

new_df = df.loc[max_indx]
# print(new_df[['number', 'title', 'text']])

prompt = f''' I am teaching web development in my sigma web development course. Here are video subtitle chunks containing video number,video title, start time in seconds, end time in seconds, the text at that time:

{new_df[['number', 'title', 'start', 'end', 'text']].to_json(orient="records")}
---------------------------------------------
{incoming_query}
User asked this question related to the video chunks, you have to answer in a human way (dont mention the above format, its just for your understanding) where and how much content is taught in which videp (in which video and what timestamp) and guide the user to go to that particular video. If user asked unrelated question, tell him that you can only answer questions related to the course.
'''

gemini_prompt = f"""
You are an AI assistant for the Sigma Web Development course.

Below are subtitle chunks retrieved from the course.

Retrieved course content:
{new_df[['number', 'title', 'start', 'end', 'text']].to_json(orient="records")}

User question:
{incoming_query}

Instructions:

1. Answer the user's question using only the retrieved course content.
2. If the question is related to the course, identify the relevant video number and video title.
3. Give the relevant timestamp using the provided start and end times.
4. Explain briefly what is taught at that timestamp.
5. Guide the user to the relevant video.
6. Do not invent video numbers, titles, timestamps, or content that is not present in the retrieved chunks.
7. If the retrieved content does not contain enough information to answer the question, clearly say that the available course chunks do not provide enough information.
8. If the question is unrelated to the Sigma Web Development course, say that you can only answer questions related to the course.
9. Answer naturally and clearly. Do not mention that you are looking at JSON, embeddings, retrieved chunks, or the RAG pipeline.
"""

with open('prompt.txt', 'w') as f:
    f.write(prompt)
    
response = inference(prompt)["response"]
# print(response)

# response = inference_gemini(gemini_prompt)
# print(response)

with open('response.txt', 'w') as f:
    f.write(response)
    
# for index, item in new_df.iterrows():
#     print(index, item['title'], item['number'], item['text'], item['start'],"-" ,item['end'])
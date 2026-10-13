import json
import boto3
from dotenv import load_dotenv
import os
import chromadb
import sqlite3

load_dotenv()

## Initiate the connection between the AWS and local python client using boto3

REGION=os.getenv("REGION")
EMBEDDING_MODEL_ID = os.getenv("EMBEDDING_MODEL_ID")

boto_client = boto3.client('bedrock-runtime', region_name = REGION)


def embed(text: str) -> list:
    '''
    This function will basically convert the given text to a mathematical representation in the form of vector
    which will carry the semantics of the text
    This will help us to relate / find the closest match.
    '''

    response = boto_client.invoke_model(
        modelId = EMBEDDING_MODEL_ID,
        body = json.dumps({"inputText": text})
    )

    embeddings = json.loads(response['body'].read())['embedding']

    return embeddings

def retreive_tables(question: str, k:int = 4) -> set:
    ## Load the collection
    collection = chromadb.PersistentClient(path=r'notebooks\chromadb').get_collection('tables')
    result = collection.query(query_embeddings=[embed(question)], n_results=k)
    response = set(result['ids'][0])

    return response

def add_fk_neighbours(tables:set) -> set:
    con = sqlite3.connect("file:shop.db?mode=ro", uri=True)
    result = set(tables)
    for table in tables:
        rows = con.execute(f"PRAGMA foreign_key_list({table})").fetchall()
        if len(rows)>0:
            for row in rows:
                result.add(row[2])
    return result


if __name__ == "__main__":

    text = "Get me the revenue for the last month ?"
    v = embed(text)
    print("The length of the vector:", len(v))
    print(v[:5])
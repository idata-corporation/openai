import os
from openai import OpenAI
import pandas as pd
import json
import PyPDF2
import singlestoredb as s2
import string

conn = s2.connect(host='svc-0c779247-ddcf-4590-a7d3-1698f8f4dcbf-dml.aws-virginia-6.svc.singlestore.com', port='3306', user='admin',
                  password='bhxgmqA72eyxwio1keUbf99qwm2qwSj6', database='vectordb')

client = OpenAI(
  api_key = os.environ.get("OPENAI_API_KEY")
)

def do_query(embedding):
  sql = "select text, dot_product(vector, JSON_ARRAY_PACK(\"%s\")) as score from myvector order by score DESC limit 1" % embedding
  with conn.cursor() as cur:
      cur.execute(sql)
      for row in cur.fetchall():
        print("===========================")
        print(row)

def get_embedding(text, model="text-embedding-3-small"):
  return client.embeddings.create(input = [text], model=model).data[0].embedding

#embeddings = get_embedding(text = 'This is a test', model='text-embedding-3-small')
#print(json.dumps(embeddings))

def ask_question():
  user_input = input("What is your question? ")
  embedding = get_embedding(user_input)
  do_query(embedding)

while True:
  ask_question()
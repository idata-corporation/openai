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

def get_embedding(text, model="text-embedding-3-small"):
  return client.embeddings.create(input = [text], model=model).data[0].embedding

#embeddings = get_embedding(text = 'This is a test', model='text-embedding-3-small')
#print(json.dumps(embeddings))

def store_embeddings(text, embeddings):
  sql = "insert into myvector (text, vector) values (\"%s\", JSON_ARRAY_PACK(\"%s\"))" % (text, embeddings)
  print(sql)
  with conn.cursor() as cur:
      cur.execute(sql)

def filter_text(text):
      filtered = ''.join([x for x in text if x in string.printable])
      filtered = filtered.replace('\r', '')
      filtered = filtered.replace('\n', ' ')
      filtered = filtered.replace('"', '')
      filtered = filtered.replace("'", '')
      return filtered

def process_pdf(filename):
  pdfFileObj = open('./10-q-8-2-23.pdf', 'rb')
  pdfReader = PyPDF2.PdfReader(pdfFileObj)
  i = 0
  while i < len(pdfReader.pages):
      pageObj = pdfReader.pages[i]
      text = pageObj.extract_text()
      filtered = filter_text(text)

      embeddings = get_embedding(filtered)
      store_embeddings(filtered, embeddings)
      i += 1
  pdfFileObj.close()


process_pdf('./10-q-8-2-23.pdf')
import uuid

from bs4 import BeautifulSoup
from langchain.embeddings import SentenceTransformerEmbeddings
from markdownify import markdownify as md

embeddings = SentenceTransformerEmbeddings(model="all-MiniLM-L6-v2")

import json

import predict_engine
import config
from config import db_global as db

# get skills for each jobs
# def populate_db_with_embeddings(jobs):
#     for job in jobs:
#         skills = get_job_skills()
#         document = { 'skills': [], 'job_id': job['job_id'] }
#         # create embedding for each job
#         for skill in skills:
#             embedding = openai.embeddings(skill)
#             document['skills'].append(embedding)

#         # insert document into vector DB
#         db.insert(document)

def get_jobs_by_ids(jobs, job_ids):
    result = []
    for id in job_ids:
        job = get_job_by_id(jobs, id)
        
        # do any data wrangling here
        cleaned_job = {
            'job_id': job['id'],
            'job_title': job['title'],
            'job_description': job['content']
        }
        result.append(cleaned_job)
    return result


def run_batch_retreival(company):
    # Get your URL ready to accept a parameter
    url = f'https://boards-api.greenhouse.io/v1/boards/{company}/jobs?content=true'
    
    try:
        response = requests.get(url)
    except:
        # In case it doesn't work
        print ("Whoops, error")
        return
        
    status_code = response.status_code
    jobs = response.json()['jobs']
    print (f"{company}: {status_code}, Found {len(jobs)} jobs")
    return jobs

def get_job_by_id(jobs, job_id):
    for job in jobs:
        if job['id'] == job_id:
            return job
    
def printOutput(output):
    print(json.dumps(output,sort_keys=True, indent=3))

def extract_relevant_info_from_jobs(jobs):
    for job in jobs:
        result = predict_engine.predict(job['job_description'])
        job['job_skills'] = result

    with open('tests/demo2_output.json', 'w') as file:
        json.dump(jobs, file, indent=4)

def create_embeddings_for_jobs(jobs):
    results = []
    if jobs:
        for job in jobs:
            embeddings_results = []
            for skill in job['job_skills']:
                embedding = embeddings.embed_query(skill)
                embeddings_results.append(embedding)
            
            job['embeddings'] = embeddings_results 

    # write skills into file
    with open('tests/demo2_output_embeddings.json', 'w') as file:
        json.dump(jobs, file, indent=4)

    return results


def select_job_ids(jobs):
    return [4992146, 4977225, 4961541, 4901909, 4977145, 4850151, 5004001, 4913783, 4954092, 4925230, 4997750, 4965052, 4961622, 4813901, 4899077]

def processJob(job_description):
    soup = BeautifulSoup(job_description, 'html.parser')
    text = soup.get_text()
    text = md(text)
    return text 

def insertEmbeddingsForAllJobs(jobs):
    try:
        for job in jobs:
            size = len(job['job_skills'])
            db.collection.add(
                documents=[skill for skill in job['job_skills']],
                metadatas=[{'job_id': job['job_id'] } for _ in range(size)],
                ids=[str(uuid.uuid4()) for _ in range(size)]
            )
    except Exception as err:
        print("Exception inserting into db: ", err)
    
"""
Run batch script - this would be done on a regular basis to fill up the 
database and keep jobs regularly updated.
"""
# company_name = 'stripe'
# all_jobs = run_batch_retreival(company_name)
# selected_job_ids = select_job_ids(all_jobs)
# my_jobs = get_jobs_by_ids(all_jobs, selected_job_ids)

with open('tests/demo2_output.json', 'r') as file:
    jobs_with_skills = json.load(file)

# jobs_with_skills = extract_relevant_info_from_jobs(my_jobs)
#jobs_with_skills_and_embeddings = create_embeddings_for_jobs(my_jobs)

# insertEmbeddingsForAllJobs(jobs_with_skills)
results = collection.query(
    query_texts=["data engineering"],
    n_results=5
)
printOutput(results)
# try:
#     insertEmbeddingsForAllJobs(jobs_with_skills_and_embeddings, db)
# except:
#     print("Could not insert document")

# Do a sanity check
# assert(db.query("AWS", n=2), [{'document': "AWS", 'score': 1}, { 'document': "AWS Cloud", 'score': 0.97 }])
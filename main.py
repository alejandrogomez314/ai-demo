# LangChain Models
from langchain.llms import OpenAI

# Standard Helpers
import pandas as pd
import requests
import time
import json
import os
from datetime import datetime



# For token counting
from langchain.callbacks import get_openai_callback
from kor.nodes import Object, Text
from kor.extraction import create_extraction_chain
from langchain.chat_models import ChatOpenAI



def pull_from_greenhouse(board_token):
    # Get your URL ready to accept a parameter
    url = f'https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true'
    
    try:
        response = requests.get(url)
    except:
        # In case it doesn't work
        print ("Whoops, error")
        return
        
    status_code = response.status_code
    jobs = response.json()['jobs']
    print (f"{board_token}: {status_code}, Found {len(jobs)} jobs")
    return jobs

def getJobFromId(jobs, job_id):
    return [item for item in jobs if item['id'] == job_id][0]

def describeJob(job_description):
    print(f"Job ID: {job_description['id']}")
    print(f"Link: {job_description['absolute_url']}")
    print(f"Updated At: {datetime.fromisoformat(job_description['updated_at']).strftime('%B %-d, %Y')}")
    print(f"Title: {job_description['title']}\n")
    print(f"Content:\n{job_description['content']}")




llm = ChatOpenAI(
    model_name="gpt-3.5-turbo", # Cheaper but less reliable
    #model_name="gpt-4",
    temperature=0,
    max_tokens=2000,
    openai_api_key=os.getenv('OPENAI_API_KEY')
)

skill_schema = Object(
    id="skills",
    attributes=[
        Text(id="skill", description="A tool, skill or programming language used at work.")
    ],
    examples=[
        (
            "Experience in working with Netsuite, or Looker a plus.",
            [
                {"skill": "Netsuite"},
                {"skill": "Looker"},
            ],
        ),
        (
           "Experience with Microsoft Azure",
            [
               {"skill": "Microsoft Azure"}
            ] 
        ),
        (
            "Experience with cloud databases and technologies",
            [
                {"skill": "cloud"},
                {"skill": "cloud databases"}
            ]
        ),
        (
           "You must know AWS to do well in the job",
            [
               {"skill": "AWS"}
            ] 
        ),
        (
           "Troubleshooting customer issues and debugging from logs (Splunk, Syslogs, etc.) ",
            [
               {"skill": "Splunk"},
            ] 
        )
    ]
)

chain = create_extraction_chain(llm, skill_schema)

# Load JSON data from file
with open('tests/demo.json', 'r') as file:
    data = json.load(file)

for job in data['jobs']:
    start_time = time.time()
    output = chain.predict_and_parse(text=job['job_description'])["data"]
    end_time = time.time()
    elapsed_time = end_time - start_time
    print("SKILLS - Elapsed time: {:.6f} seconds".format(elapsed_time))
    job['job_skills'] = output

# # write skills into file
with open('tests/demo_output.json', 'w') as file:
    json.dump(data, file, indent=4)

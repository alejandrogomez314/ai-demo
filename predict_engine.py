
# For token counting
from langchain.callbacks import get_openai_callback
from langchain.chat_models import ChatOpenAI

from kor.extraction import create_extraction_chain
from kor.nodes import Object, Text

from dotenv import load_dotenv
import os
import json
import time
from langchain.embeddings import SentenceTransformerEmbeddings 
embeddings = SentenceTransformerEmbeddings(model="all-MiniLM-L6-v2")

from config import db_global as db

with open('tests/demo2.json', 'r') as file:
    jobs_data = json.load(file)

# Load values from .env file
load_dotenv()

llm = ChatOpenAI(
    model_name="gpt-3.5-turbo", # Cheaper but less reliable
    #model_name="gpt-4",
    temperature=0,
    max_tokens=800,
    openai_api_key=os.getenv('OPENAI_API_KEY')
)

"""
Get the total cost and token count of a call to extract skills 
from a resume.
"""
def getPredictionCost(chain, text):
    with get_openai_callback() as cb:
        chain.predict_and_parse(text=text)
        return {
            "Total Tokens": cb.total_tokens,
            "Prompt Token": cb.prompt_tokens,
            "Completion Tokens": cb.completion_tokens,
            "Successful Requests": cb.successful_requests,
            "Total Cost (USD)":cb.total_cost
        }
"""
Function to handle the file data and perform prediction
predict only retrieves skills from resume. Potential additions include:
- generate related keywords for matching
- analyze job post description to resume similarity
- ...
"""

def predict(text):

    # Create a chain where multiple model calls can be chained into it. 
    chain = create_extraction_chain(llm, skill_schema)

    # Extract entities out of resume 
    start_time = time.time()
    output = chain.predict_and_parse(text=text)["data"]
    end_time = time.time()

    elapsed_time = end_time - start_time
    print("Elapsed time: {:.6f} seconds".format(elapsed_time))

    normalized_skills = normalize(output)

    return normalized_skills

def normalize(data):
    if data and data['skills']:
        return [item['skill'].lower() if 'skill' in item else item for item in data['skills']]
    return data

def printOutput(output):
    print(json.dumps(output,sort_keys=True, indent=3))

def match_skills(resume_skills):
    matched_jobs = {}
    for skill in resume_skills:

        results = db.query(query_texts=skill, n_results=3) 

        for i,item in enumerate(results['metadatas'][0]):
            if item['job_id'] in matched_jobs:
                matched_jobs[item['job_id']] += results['distances'][0][i]
            else:
                matched_jobs[item['job_id']] = results['distances'][0][i]
    
    # sorted by total distance
    sorted_result = dict(sorted(matched_jobs.items(), key=lambda x: x[1], reverse=True))

    # return jobs for five highest-scoring job distances
    final_result = []
    for i,result in enumerate(sorted_result):
        if i == 4:
            break
        final_result.append([job for job in jobs_data if job['job_id'] == result][0])

    return final_result

education_schema = Object(
    id="education",
    attributes=[
        Text(id="education", description="Get college degree (bachelors, masters or Phd). A college, company or title is NOT a degree and should NOT be included.")
    ],
    examples=[
        (
            "MS in Software Engineering from Villanova University",
            [
                {"education": "M.S. in Software Engineering"},
            ],
       ),
       (
            "Bachelor of arts in English and Economics with a minor in Computer Science",
            [
                { "education": "B.A. in English" }, 
                { "education": "B.A. in Economics" },
            ]
       ),
        (
            "Bachelors in Computer Science or similar",
            [
                { "education": "B.S. in Computer Science "}
            ]
        ),
        (
            "Masters preferred",
            [
                { "education": "Masters degree" }
            ]
        )
    ]
)

skill_schema = Object(
    id="skills",
    attributes=[
        Text(id="skill", description="A tool, skill, software, or programming language used at work. Only respond with { 'skill': '<answer>' }")
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
        ),
        (
            "Build new infrastructure, services, and features that operate at scale",
            [
                {"skill": "infrastructure"},
                {"skill": "scalable systems"}
            ]
        ),
        (
            "Have experience with distributed computing systems",
            [
                {"skill": "distributed systems"}
            ]
        ),
        (
            "Ensure that our services are scalable, extensible, reliable, and performant which meet SLAs for our users.",
            [
                {"skill": "scalable systems"},
                {"skill": "reliable systems"},
                {"skill": "extensible systems"},
                {"skill": "performance engineering"}
            ]
        )
    ]
)

resume_schema = Object(
    id="resume",
    attributes=[
        education_schema,
        skill_schema
    ]
)
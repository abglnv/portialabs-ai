# Portialabs AI

We have created an AI agent that checks services for the latest vulnerabilities from sploitus.com based on IP address and domain.

With the help of portiaai sdk we take the latest vulnerabilities once a week, take services from the database that may be vulnerable, generate a lambda function to check the service for vulnerability, deploy it and run the check. Most of the checks work through http requests

Installation:

git clone https://github.com/rendizi/portialabs-ai

pip install -r requirements.txt 

uvicorn main:app 

----or------

docker build -t ai_agent .
docker run ai_agent


Technologies used:

python, fastapi, mongodb, aws, portialabs ai, openai, next.js, ts.

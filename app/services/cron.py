from fake_useragent import UserAgent
import httpx 
from pymongo import MongoClient
import subprocess
import json 
from app.portia.portia import PortiaInstance
import boto3
import zipfile
import os
import re 

lambda_client = boto3.client("lambda", region_name="us-east-1")

MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["portialabs"]
exploits_collection = db["exploits"]
ua = UserAgent()

def fetch_exploits_of_week():
    url = "https://sploitus.com/top"
    random_user_agent = ua.random

    response = httpx.get(url, headers={"User-Agent": random_user_agent})
    if response.status_code == 200:
        data = response.json()
        if "top" in data:
            return data["top"]
        else:
            print("No exploits found in the response.")
    else:
        print(f"Failed to fetch data: {response.status_code}")

    return 

def fetch_details(id: str):
    """
    Fetch detailed information about an exploit from Sploitus API using curl.

    Args:
        id (str): The ID of the exploit to fetch details for.

    Returns:
        dict: The JSON response from the Sploitus API if successful, otherwise None.
    """
    # Construct the curl command
    curl_command = [
        "curl",
        "-X", "POST",
        "https://sploitus.com/search",
        "-H", "Content-Type: application/json",
        "-d", json.dumps({
            "type": "exploits",
            "sort": "default",
            "query": id,
            "title": False,
            "offset": 0
        })
    ]

    try:
        # Execute the curl command
        result = subprocess.run(curl_command, capture_output=True, text=True, check=True)

        # Parse the JSON response
        response_json = json.loads(result.stdout)
        return response_json
    except subprocess.CalledProcessError as e:
        print(f"Error executing curl: {e.stderr}")
    except json.JSONDecodeError:
        print("Failed to parse JSON response.")
    return None

def save_exploits(exploits):
    """
    Save exploits to the MongoDB database.
    
    Args:
        exploits (list): A list of exploit dictionaries with fields:
                         title, score, href, type, published, id, source, language.
    """
    for exploit in exploits:
        existing_exploit = exploits_collection.find_one({"id": exploit["id"]})
        if not existing_exploit:
            exploits_collection.insert_one({
                "title": exploit["title"],
                "score": exploit["score"],
                "href": exploit["href"],
                "type": exploit["type"],
                "published": exploit["published"],
                "id": exploit["id"],
                "source": exploit["source"],
                "language": exploit["language"]
            })
        else:
            print(f"Exploit with ID {exploit['id']} already exists. Skipping.")

def upload_lambda(name, code, description, exploit_id):
    """
    Upload the Python function to AWS Lambda and invoke it.

    Args:
        name (str): Name of the Lambda function.
        code (str): Python function code.
        description (str): Description of the Lambda function.
        exploit_id (str): ID of the exploit.

    Returns:
        dict: Response from the Lambda invocation.
    """
    temp_dir = f"/tmp/{name}"
    os.makedirs(temp_dir, exist_ok=True)

    lambda_file_path = os.path.join(temp_dir, "lambda_function.py")
    with open(lambda_file_path, "w") as f:
        f.write(code)

    zip_file_path = os.path.join(temp_dir, f"{name}.zip")
    with zipfile.ZipFile(zip_file_path, "w") as zipf:
        zipf.write(lambda_file_path, arcname="lambda_function.py")

    try:
        response = lambda_client.create_function(
            FunctionName=name,
            Runtime="python3.9",
            Role="arn:aws:iam::YOUR_ACCOUNT_ID:role/YOUR_LAMBDA_ROLE",
            Handler="lambda_function.lambda_handler",
            Code={"ZipFile": open(zip_file_path, "rb").read()},
            Description=description,
            Timeout=30,
            MemorySize=128,
        )
        print(f"Lambda function {name} created successfully.")
    except lambda_client.exceptions.ResourceConflictException:
        response = lambda_client.update_function_code(
            FunctionName=name,
            ZipFile=open(zip_file_path, "rb").read(),
        )
        print(f"Lambda function {name} updated successfully.")

    # invoke_response = lambda_client.invoke(
    #     FunctionName=name,
    #     InvocationType="RequestResponse",
    #     Payload=json.dumps({"exploit_id": exploit_id}),
    # )

    os.remove(lambda_file_path)
    os.remove(zip_file_path)
    os.rmdir(temp_dir)

    return True 

    # return json.loads(invoke_response["Payload"].read())

def extract_and_parse_json(raw_output):
    # Check if the output contains markdown code fences (triple backticks)
    if '```' in raw_output:
        # Try to extract the JSON block inside markdown code fences
        match = re.search(r'```(?:json)?\s*(\{.*\})\s*```', raw_output, re.DOTALL)
        if match:
            json_str = match.group(1)
        else:
            # Fallback: attempt to remove all backticks and then extract JSON
            json_str = raw_output.replace('```', '')
    else:
        # If no markdown formatting is detected, attempt to extract the JSON object directly
        match = re.search(r'(\{.*\})', raw_output, re.DOTALL)
        if match:
            json_str = match.group(1)
        else:
            raise ValueError("No valid JSON object found in the output")

    # Attempt to parse the extracted JSON string
    try:
        parsed_json = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError("Extracted text is not valid JSON") from e

    return parsed_json

def run_cron():
    """
    Run the cron job to fetch and save exploits of the week.
    """
    print("Running cron job...")
    top_exploits = fetch_exploits_of_week()
    print(top_exploits)
    if top_exploits:
        exploits = []
        for exploit in top_exploits:
            details = fetch_details(exploit["id"])
            if details and "exploits" in details and len(details["exploits"]) > 0:
                exploits.append({
                    "title": details["exploits"][0]["title"],
                    "score": details["exploits"][0]["score"],
                    "href": details["exploits"][0]["href"],
                    "type": details["exploits"][0]["type"],
                    "published": details["exploits"][0]["published"],
                    "id": details["exploits"][0]["id"],
                    "source": details["exploits"][0]["source"],
                    "language": details["exploits"][0]["language"]
                })

        portia = PortiaInstance()

        technologies_str = portia.run(f"""
            You are a security researcher.
            You are given a list of exploits.
            Your task is to analyze the exploits and provide affected technologies of each exploit.
            The exploits are in JSON format:
            {json.dumps(exploits)}
            Provide the affected technologies for each exploit in JSON format.
            The output should be a list of dictionaries with the following keys:
            - title: The title of the exploit
            - affected_technologies: A list of affected technologies
            Example:
            [
                {{
                    "title": "Exploit Title 1",
                    "affected_technologies": ["Technology 1", "Technology 2"]
                }},
                {{
                    "title": "Exploit Title 2",
                    "affected_technologies": ["Technology 3"]
                }}
            ]
            The affected technologies should be relevant to the exploit.
            If you cannot find any affected technologies, return an empty list.
            If you cannot find any exploits, return an empty list.
            If you cannot find any affected technologies for an exploit, return an empty list.
            The output should be in JSON format. No markdown or other formatting.
            Do not include any explanations or additional information.
        """)
        print(technologies_str)
        technologies = json.loads(technologies_str)

        for i, exploit in enumerate(exploits):
            run = portia.run(f"""
                You are a security researcher provided with exploit information in JSON format (available in the variable "exploit"). Your goal is to analyze this exploit and generate a Python function that tests services based on the exploit.

There are two testing scenarios:

    Remote Testing:

        The Python function must be named "lambda_handler" and accept two arguments: event and context.

        The event object will provide either an IP address or a domain of the service (only one of these will be provided).

    Local Testing:

        The Python function must be named "lambda_handler" with no arguments.

        Use the IP address "127.0.0.1" for testing.

After creating the Python function, your output must be a JSON object with these keys:

    code: A string containing the complete Python function code.

    type: The testing type ("local" or "remote").

    description: A brief explanation of why the test will work.

    name: The function’s name (should be "lambda_handler").

    id: The exploit's identifier from the provided exploit information.

The final output must be in valid JSON format with exactly the keys listed above, and no markdown formatting, explanations, or extra information. IN ANY CIRCUMSTANCES, DO NOT INCLUDE ANY MARKDOWN FORMATTING OR ADDITIONAL TEXT. ```'S ARE BANNED 
            """)
            if run.startswith("```json"):
                run = run[7:-3]
            if run.endswith("```"):
                run = run[:-3]
            print(run)
            run = json.loads(run)
            print(run)
            outputs = run['outputs']
            print(outputs)
            final_output = outputs['final_output']
            print(final_output)
            val = json.loads(final_output['value'])
            print(val)
            if val.startsWith("```json"):
                val = val[7:-3]
            if val.endswith("```"):
                val = val[:-3]
            summary = json.loads(val)
            # plan_run_json = json.loads(plan_run_json)
            # print(plan_run_json.outputs.final_output)
            print(241)
            type = summary["type"]
            code = summary["code"]
            description = summary["description"]
            name = summary["name"]
            exploit_id = summary["id"]

            if type == "remote":
                upload_lambda(name, code, description, exploit_id)

            break 

        # save_exploits(exploits)
        print("Exploits saved successfully.")
    else:
        print("No new exploits found.")
    print("Cron job completed.")
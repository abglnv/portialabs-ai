from fake_useragent import UserAgent
import httpx 
from pymongo import MongoClient
import subprocess
import json 
from app.portia.portia import PortiaInstance
import boto3
import zipfile
import os

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
            plan = portia.plan(f"""
                You are a security researcher.
                You are given an exploit information.
                Your task is to analyze the exploit and based on description generate python function to test services on this exploit.
                There are 2 types of testing- local and remote. 
                In remote we provide the python code ip address and domain of the service. 
                In local we run the code on the server.
                Python code will be ran on AWS Lambda.
                The exploit is in JSON format:
                {exploit}
                At the end you need to return json with following keys:
                - code: python function code  
                - type: type of testing (local or remote)
                - description: why this test will work. 
                - name: name of python function code 
                - id: id of the exploit
                The output should be in JSON format. No markdown or other formatting.
                Do not include any explanations or additional information.
                
                If remote, your function should be like this:
                def lambda_handler(event, context):
                               
                you can access ip and domain of service through event. One of this 2 will be provided.
                if local, your function should not take any arguments. it should be called lambda_handler aswell. As ip just use 127.0.0.1
            """)
            print(plan)
            plan_run_json = portia.run_plan(plan)
            print(plan_run_json)
            break 
            print(plan_run_json)
            type = plan_run_json["type"]
            code = plan_run_json["code"]
            description = plan_run_json["description"]
            name = plan_run_json["name"]
            exploit_id = plan_run_json["id"]

            if type == "remote":
                upload_lambda(name, code, description, exploit_id)

            

        # save_exploits(exploits)
        print("Exploits saved successfully.")
    else:
        print("No new exploits found.")
    print("Cron job completed.")
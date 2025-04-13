import os
import httpx
from pydantic import BaseModel, Field
from portia.errors import ToolHardError, ToolSoftError
from portia.tool import Tool, ToolRunContext
from typing import Literal
from fake_useragent import UserAgent
import boto3
import zipfile
import json

ua = UserAgent()

class FunctionsToolSchema(BaseModel):
    """Input for AWSTool."""

class FunctionsTool(Tool):
    """FunctionsTool for DB and AWS."""
    name: str = "sploitus_search"
    description: str = "Functions tool for exploit search"
    args_schema: type[BaseModel] = FunctionsToolSchema
    output_schema: tuple[str, str] = ("str", "Dict output of the DB and AWS.")

    def run(
        self,
        _: ToolRunContext, 
        query: str, 
        sortBy: Literal["default", "date", "score"], 
        offset: int,
        type: Literal["exploits", "tools"]
    ) :
        return 
    
    def upload_lambda(
        self,
        context: ToolRunContext,
        name: str,
        code: str,
        description: str,
        exploit_id: str
    ) -> dict:
        """
        Upload the Python function to AWS Lambda and invoke it.

        Args:
            context (ToolRunContext): Context for the tool run.
            name (str): Name of the Lambda function.
            code (str): Python function code.
            description (str): Description of the Lambda function.
            exploit_id (str): ID of the exploit.

        Returns:
            dict: Response from the Lambda invocation.
        """
        try:
            # Create temporary directory and files
            temp_dir = f"/tmp/{name}"
            os.makedirs(temp_dir, exist_ok=True)

            lambda_file_path = os.path.join(temp_dir, "lambda_function.py")
            with open(lambda_file_path, "w") as f:
                f.write(code)

            zip_file_path = os.path.join(temp_dir, f"{name}.zip")
            with zipfile.ZipFile(zip_file_path, "w") as zipf:
                zipf.write(lambda_file_path, arcname="lambda_function.py")

            # Initialize AWS Lambda client
            lambda_client = boto3.client("lambda")

            # Create or update the Lambda function
            try:
                response = lambda_client.create_function(
                    FunctionName=name,
                    Runtime="python3.9",
                    Role="arn:aws:lambda:eu-central-1:339713122265:function:security",
                    Handler="lambda_function.lambda_handler",
                    Code={"ZipFile": open(zip_file_path, "rb").read()},
                    Description=description,
                    Timeout=30,
                    MemorySize=128,
                )
                context.log.info(f"Lambda function {name} created successfully.")
            except lambda_client.exceptions.ResourceConflictException:
                response = lambda_client.update_function_code(
                    FunctionName=name,
                    ZipFile=open(zip_file_path, "rb").read(),
                )
                context.log.info(f"Lambda function {name} updated successfully.")

            # Optionally invoke the Lambda function
            invoke_response = lambda_client.invoke(
                FunctionName=name,
                InvocationType="RequestResponse",
                Payload=json.dumps({"exploit_id": exploit_id}),
            )
            invoke_payload = json.loads(invoke_response["Payload"].read())

            # Clean up temporary files
            os.remove(lambda_file_path)
            os.remove(zip_file_path)
            os.rmdir(temp_dir)

            return {
                "status": "success",
                "lambda_response": response,
                "invoke_response": invoke_payload,
            }

        except Exception as e:
            context.log.error(f"Error in upload_lambda: {str(e)}")
            raise ToolHardError(f"Failed to upload Lambda function: {str(e)}")
    
    def save_to_db():
        return
    

from dotenv import load_dotenv
from portia import (
    Portia,
    default_config,
    example_tool_registry,
    PortiaToolRegistry,
)
from .sploitus_tool import SploitusTool
import json 
from portia.open_source_tools.search_tool import SearchTool
from portia import InMemoryToolRegistry
load_dotenv()

class PortiaInstance:
    _instance = None  

    def __new__(cls, *args, **kwargs):
        """Ensure only one instance of PortiaInstance is created."""
        if not cls._instance:
            custom_tool_registry = InMemoryToolRegistry.from_local_tools(
                [
                    SploitusTool(id="unique_tool_id")
                ],
            )
            # Instantiate a Portia instance. Load it with the example tools and Portia's github search tool.
            cls._instance = super(PortiaInstance, cls).__new__(cls, *args, **kwargs)
            cls._instance.portia = Portia(tools=example_tool_registry+custom_tool_registry)  
        return cls._instance

    def run(self, input: str, dict=True):
        """
        Run the Portia instance with the provided input.
        """
        try:
            plan_run = self.portia.run(input)
            return plan_run.model_dump_json(indent=2) if dict else plan_run
        except Exception as e:
            raise e
        
    def run_plan(self, plan):
        try:
            # Run the generated plan
            plan_run = self.portia.run_plan(plan)
            return json.loads(plan_run)
            # return plan_run.model_dump_json(indent=2)
        except Exception as e:
            raise e

    def plan(self, input: str):
        """
        Get the plan for the provided input.
        """
        try:
            plan = self.portia.plan(input)
            return plan
        except Exception as e:
            raise e
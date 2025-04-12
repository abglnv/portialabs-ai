import os
import httpx
from pydantic import BaseModel, Field
from portia.errors import ToolHardError, ToolSoftError
from portia.tool import Tool, ToolRunContext
from typing import Literal
from fake_useragent import UserAgent

ua = UserAgent()

class FunctionsToolSchema(BaseModel):
    """Input for SploitusTool."""
    query: str = Field(..., description="Query for exploit type")
    sortBy: Literal["default", "date", "score"] = Field(..., description="Sort results by (default, date, or score)")
    offset: int = Field(0, description="Offset for pagination")
    type: Literal["exploits", "tools"] = Field(..., description="Type of search (exploits or tools)")

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
    
    def upload_aws():
        return 
    
    def save_to_db():
        return
    

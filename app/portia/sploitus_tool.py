import os
import httpx
from pydantic import BaseModel, Field
from portia.errors import ToolHardError, ToolSoftError
from portia.tool import Tool, ToolRunContext
from typing import Literal
from fake_useragent import UserAgent

ua = UserAgent()

class SploitusToolSchema(BaseModel):
    """Input for SploitusTool."""
    query: str = Field(..., description="Query for exploit type")
    sortBy: Literal["default", "date", "score"] = Field(..., description="Sort results by (default, date, or score)")
    offset: int = Field(0, description="Offset for pagination")
    type: Literal["exploits", "tools"] = Field(..., description="Type of search (exploits or tools)")

class SploitusTool(Tool):
    """SploitusTool for Sploitus API."""
    name: str = "sploitus_search"
    description: str = "Sploitus tool for exploit search"
    args_schema: type[BaseModel] = SploitusToolSchema
    output_schema: tuple[str, str] = ("dict", "Dict output of the Sploitus API search including total exploits and a list of exploits.")

    def run(
        self,
        _: ToolRunContext, 
        query: str, 
        sortBy: Literal["default", "date", "score"], 
        offset: int,
        type: Literal["exploits", "tools"]
    ) -> dict:
        """Run the SploitusTool.
        
        Builds the request payload, sets a random User-Agent header,
        makes the API call to Sploitus, and returns the parsed JSON response.
        Expected response is a dict like:
        {
            "exploits_total": 200,
            "exploits": [
                {
                    "title": "...",
                    "score": ...,
                    "href": "...",
                    "type": "...",
                    "published": "...",
                    "id": "...",
                    "source": "...",
                    "language": "..."
                },
                ...
            ]
        }
        """
        request_body = {
            "offset": offset,
            "query": query,
            "sort": sortBy,
            "title": False, 
            "type": type
        }
        random_user_agent = ua.random

        url = "https://sploitus.com/search"

        response = httpx.post(url, json=request_body, headers={"User-Agent": random_user_agent})
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 400:
            raise ToolSoftError(f"Bad request: {response.text}")
        else:
            raise ToolHardError(f"Error: {response.status_code} - {response.text}")

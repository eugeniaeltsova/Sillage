from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import json
import traceback

from app.tools import (
    tool_search_perfumes,
    tool_compare_perfumes,
    tool_get_perfume_details,
    perfume_names,
    perfume_name_to_id
)
from app.utils import qdrant_client, openai_client, COLLECTION_NAME
from qdrant_client.models import PayloadSchemaType

load_dotenv(r"C:\Perfume_Seeker\.env")

# ── Startup logic ─────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load perfume names from Qdrant into memory
    print("Loading perfume names from Qdrant...")
    offset = None
    all_points = []

    while True:
        results, offset = qdrant_client.scroll(
            collection_name=COLLECTION_NAME,
            with_payload=["Perfume"],
            limit=1000,
            offset=offset
        )
        all_points.extend(results)
        if offset is None:
            break

    for point in all_points:
        name = point.payload.get("Perfume")
        if name:
            perfume_names.append(name)
            perfume_name_to_id[name] = point.id

    print(f"Loaded {len(perfume_names)} perfume names into memory")

    # Create payload indexes for filtering
    print("Creating payload indexes...")
    indexable_fields = [
        ("Gender", PayloadSchemaType.KEYWORD),
        ("Brand", PayloadSchemaType.KEYWORD),
        ("Perfumer1", PayloadSchemaType.KEYWORD),
        ("Year", PayloadSchemaType.INTEGER),
        ("notes_combined", PayloadSchemaType.TEXT),
    ]
    for field_name, field_type in indexable_fields:
        qdrant_client.create_payload_index(
            collection_name=COLLECTION_NAME,
            field_name=field_name,
            field_schema=field_type
        )
    print("Indexes created")

    yield  # app runs here

# ── FastAPI app ───────────────────────────────────────────────────────────────
app = FastAPI(title="Sillage — Fragrance Discovery API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    traceback.print_exc()  # prints full traceback to terminal
    return JSONResponse(
        status_code=500,
        content={"error": str(exc)}
    )

# ── Tool definitions for GPT-4.1 ──────────────────────────────────────────────
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "tool_search_perfumes",
            "description": "Search the fragrance database semantically. Call this when the user is looking for fragrance recommendations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "Rich scent profile description extracted from the conversation"
                    },
                    "referenced_perfume_names": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of reference perfume names mentioned by the user"
                    },
                    "gender": {
                        "type": "string",
                        "enum": ["men", "women", "unisex"],
                        "description": "Gender filter if explicitly stated"
                    },
                    "year_from": {
                        "type": "integer",
                        "description": "Minimum release year filter"
                    },
                    "year_to": {
                        "type": "integer",
                        "description": "Maximum release year filter"
                    },
                    "brand": {
                        "type": "string",
                        "description": "Brand filter if explicitly requested"
                    },
                    "perfumer": {
                        "type": "string",
                        "description": "Perfumer filter if explicitly mentioned"
                    },
                    "exclude_brands": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Brands to exclude from results"
                    },
                    "exclude_perfumers": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Perfumers to exclude from results"
                    },
                    "exclude_notes": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Notes or accords to exclude from results"
                    },
                    "top_n": {"type": "integer", "description": "Number of results to return, default 4"}
                },
                "required": ["description"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "tool_compare_perfumes",
            "description": "Compare two perfumes side by side. Call this when the user asks to compare two specific fragrances.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name_a": {
                        "type": "string",
                        "description": "Name of the first perfume"
                    },
                    "name_b": {
                        "type": "string",
                        "description": "Name of the second perfume"
                    }
                },
                "required": ["name_a", "name_b"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "tool_get_perfume_details",
            "description": "Retrieve full details of a specific perfume. Call this when the user asks about a specific fragrance.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name of the perfume"
                    }
                },
                "required": ["name"]
            }
        }
    }
]

# ── Tool dispatcher ───────────────────────────────────────────────────────────
def dispatch_tool(tool_name: str, tool_args: dict) -> str:
    if tool_name == "tool_search_perfumes":
        result = tool_search_perfumes(**tool_args)
    elif tool_name == "tool_compare_perfumes":
        result = tool_compare_perfumes(**tool_args)
    elif tool_name == "tool_get_perfume_details":
        result = tool_get_perfume_details(**tool_args)
    else:
        result = {"error": f"Unknown tool: {tool_name}"}
    return json.dumps(result, ensure_ascii=False)

# ── System prompt ─────────────────────────────────────────────────────────────
with open(r"C:\Perfume_Seeker\app\system_prompt.txt", "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()

# ── Request/Response models ───────────────────────────────────────────────────
class ChatRequest(BaseModel):
    messages: list[dict]  # full conversation history from the frontend

class ChatResponse(BaseModel):
    reply: str
    messages: list[dict]  # updated conversation history to send back

# ── Chat endpoint ─────────────────────────────────────────────────────────────
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + request.messages

    # Agentic loop — keep running until no more tool calls
    max_iterations = 10
    for _ in range(max_iterations):
        response = openai_client.chat.completions.create(
            model="gpt-4.1",
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0.2
        )

        message = response.choices[0].message

        # No tool calls — agent has a final reply
        if not message.tool_calls:
            reply = message.content
            messages.append({"role": "assistant", "content": reply})
            return ChatResponse(
                reply=reply,
                messages=messages[1:]  # strip system prompt before returning
            )

        # Tool calls — execute each and feed results back
        # Convert to dict for serialisation
        tool_calls_dict = [
            {
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments
                }
            }
            for tc in message.tool_calls
        ]
        messages.append({
            "role": "assistant",
            "content": message.content,
            "tool_calls": tool_calls_dict
        })

        for tool_call in message.tool_calls:
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)
            tool_result = dispatch_tool(tool_name, tool_args)

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": tool_result
            })

    raise HTTPException(status_code=500, detail="Agent loop exceeded maximum iterations.")

# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {
        "status": "ok",
        "perfumes_loaded": len(perfume_names)
    }
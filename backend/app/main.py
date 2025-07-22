# /*********************************************************************************************************************
# *  Copyright 2025 Amazon.com, Inc. or its affiliates. All Rights Reserved.                                           *
# *                                                                                                                    *
# *  Licensed under the Amazon Software License (the "License"). You may not use this file except in compliance        *
# *  with the License. A copy of the License is located at                                                             *
# *                                                                                                                    *
# *      http://aws.amazon.com/asl/                                                                                    *
# *                                                                                                                    *
# *  or in the "license" file accompanying this file. This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES *
# *  OR CONDITIONS OF ANY KIND, express or implied. See the License for the specific language governing permissions    *
# *  and limitations under the License.                                                                                *
# **********************************************************************************************************************/

"""
FastAPI WebSocket Server for Virtual Cloud Operations Assistant

This module implements a WebSocket server using FastAPI that handles real-time audio communication
between clients and an AI cloud operations assistant powered by AWS Nova Sonic. It processes audio streams,
manages transcription, and coordinates responses through a pipeline architecture.

Key Components:
- WebSocket endpoint for real-time audio streaming
- Audio processing pipeline with VAD (Voice Activity Detection)
- Integration with AWS Nova Sonic LLM service
- Context management for conversation history
- Credential management for AWS services

Dependencies:
- FastAPI for WebSocket server
- Pipecat for audio processing pipeline
- AWS Bedrock for LLM services
- Silero VAD for voice activity detection

Environment Variables:
- AWS_CONTAINER_CREDENTIALS_RELATIVE_URI: URI for AWS container credentials
- AWS_ACCESS_KEY_ID: AWS access key
- AWS_SECRET_ACCESS_KEY: AWS secret key
- AWS_SESSION_TOKEN: AWS session token
"""

import asyncio
import json
import base64
import traceback
import boto3
import os
from datetime import datetime
from pathlib import Path

# Import knowledge base integration
from kb_integration import KnowledgeBaseEnhancer, get_kb_information

from pipecat.adapters.schemas.function_schema import FunctionSchema
from pipecat.adapters.schemas.tools_schema import ToolsSchema
from pipecat.audio.vad.silero import SileroVADAnalyzer, VADParams
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
# from pipecat.services.aws_nova_sonic.aws import AWSNovaSonicLLMService, Params
from aws import AWSNovaSonicLLMService, Params
from pipecat.services.llm_service import FunctionCallParams
from pipecat.transports.base_transport import BaseTransport, TransportParams
from pipecat.transports.network.fastapi_websocket import FastAPIWebsocketTransport, FastAPIWebsocketParams
from pipecat.serializers.plivo import PlivoFrameSerializer
from pipecat.processors.logger import FrameLogger
from pipecat.processors.transcript_processor import TranscriptProcessor

from base64_serializer import Base64AudioSerializer

SAMPLE_RATE = 16000
API_KEY = "vba_secure_api_key_2025_07_22" # Custom API key for the virtual banking assistant

def update_dredentials():
    """
    Updates AWS credentials by fetching from ECS container metadata endpoint.
    Used in containerized environments to maintain fresh credentials.
    """
    try:
        uri = os.environ.get("AWS_CONTAINER_CREDENTIALS_RELATIVE_URI")
        if uri:
            print("Fetching fresh AWS credentials for Bedrock client", flush=True)
            with httpx.Client() as client:
                response = client.get(f"http://169.254.170.2{uri}")
                if response.status_code == 200:
                    creds = response.json()
                    os.environ["AWS_ACCESS_KEY_ID"] = creds["AccessKeyId"]
                    os.environ["AWS_SECRET_ACCESS_KEY"] = creds["SecretAccessKey"]
                    os.environ["AWS_SESSION_TOKEN"] = creds["Token"]
                    print("AWS credentials refreshed successfully", flush=True)
                else:
                    print(f"Failed to fetch fresh credentials: {response.status_code}", flush=True)
    except Exception as e:
        print(f"Error refreshing credentials: {str(e)}", flush=True)

# Import account functions
from account_functions import get_account_info, list_accounts, get_accounts_by_classification, get_accounts_by_status, get_total_cost, get_account_provisioning_date, get_accounts_by_year

# Create function schemas
account_function = FunctionSchema(
    name="get_account_info",
    description="Get information about an AWS account.",
    properties={
        "account_id": {
            "type": "string",
            "description": "The AWS account ID or name to look up information for.",
        }
    },
    required=["account_id"],
)

list_accounts_function = FunctionSchema(
    name="list_accounts",
    description="List all AWS accounts.",
    properties={},
    required=[],
)

classification_function = FunctionSchema(
    name="get_accounts_by_classification",
    description="Get AWS accounts by classification.",
    properties={
        "classification": {
            "type": "string",
            "description": "The classification to filter accounts by (e.g., Class-1, Class-2, Class-3).",
        }
    },
    required=["classification"],
)

status_function = FunctionSchema(
    name="get_accounts_by_status",
    description="Get AWS accounts by status.",
    properties={
        "status": {
            "type": "string",
            "description": "The status to filter accounts by (ACTIVE or SUSPENDED).",
        }
    },
    required=["status"],
)

cost_function = FunctionSchema(
    name="get_total_cost",
    description="Get total cost of all AWS accounts.",
    properties={},
    required=[],
)

provisioning_date_function = FunctionSchema(
    name="get_account_provisioning_date",
    description="Get provisioning date for a specific AWS account.",
    properties={
        "account_id": {
            "type": "string",
            "description": "The AWS account ID or name to look up provisioning date for.",
        }
    },
    required=["account_id"],
)

accounts_by_year_function = FunctionSchema(
    name="get_accounts_by_year",
    description="Get number of AWS accounts provisioned in a specific year.",
    properties={
        "year": {
            "type": "string",
            "description": "The year to filter accounts by (e.g., '2019').",
        }
    },
    required=["year"],
)

kb_function = FunctionSchema(
    name="get_kb_information",
    description="Get information from the knowledge base about AWS accounts, policies, or cloud operations.",
    properties={
        "query": {
            "type": "string",
            "description": "The query to search for in the knowledge base.",
        }
    },
    required=["query"],
)

# Create tools schema
tools = ToolsSchema(standard_tools=[
    account_function, 
    list_accounts_function, 
    classification_function,
    status_function,
    cost_function,
    provisioning_date_function,
    accounts_by_year_function,
    kb_function
])

async def setup(websocket: WebSocket):
    """
    Sets up the audio processing pipeline and WebSocket connection.
    
    Args:
        websocket: The WebSocket connection to set up

    Configures:
    - Audio transport with VAD and transcription
    - AWS Nova Sonic LLM service
    - Context management
    - Event handlers for client connection/disconnection
    """
    update_dredentials()
    
    # Read system instruction from prompt.txt
    base_instruction = Path('prompt.txt').read_text()
    
    # Initialize knowledge base enhancer with hardcoded KB ID
    kb_enhancer = KnowledgeBaseEnhancer(kb_id="KCZTEHHZFA")
    
    # Enhance system prompt with knowledge base instructions
    enhanced_instruction = kb_enhancer.enhance_system_prompt(base_instruction)
    
    system_instruction = enhanced_instruction + f"\n{AWSNovaSonicLLMService.AWAIT_TRIGGER_ASSISTANT_RESPONSE_INSTRUCTION}"

    # Configure WebSocket transport with audio processing capabilities
    transport = FastAPIWebsocketTransport(websocket, FastAPIWebsocketParams(
        serializer=Base64AudioSerializer(),
        audio_in_enabled=True,
        audio_out_enabled=True,
        add_wav_header=False,
        vad_analyzer=SileroVADAnalyzer(
            params=VADParams(stop_secs=0.5)
        ),
        transcription_enabled=True
    ))

    # Configure AWS Nova Sonic parameters
    params = Params()
    params.input_sample_rate = SAMPLE_RATE
    params.output_sample_rate = SAMPLE_RATE

    # Initialize LLM service
    llm = AWSNovaSonicLLMService(
        secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        session_token=os.getenv("AWS_SESSION_TOKEN"),
        region='us-east-1',
        voice_id="tiffany",  # Available voices: matthew, tiffany, amy
        params=params
    )

    # Register functions for function calls
    llm.register_function("get_account_info", get_account_info)
    llm.register_function("list_accounts", list_accounts)
    llm.register_function("get_accounts_by_classification", get_accounts_by_classification)
    llm.register_function("get_accounts_by_status", get_accounts_by_status)
    llm.register_function("get_total_cost", get_total_cost)
    llm.register_function("get_account_provisioning_date", get_account_provisioning_date)
    llm.register_function("get_accounts_by_year", get_accounts_by_year)
    llm.register_function("get_kb_information", get_kb_information)

    # Set up conversation context
    context = OpenAILLMContext(
        messages=[
            {"role": "system", "content": f"{system_instruction}"},
        ],
        tools=tools,
    )
    context_aggregator = llm.create_context_aggregator(context)

    # Create transcript processor
    transcript = TranscriptProcessor()

    # Configure processing pipeline
    pipeline = Pipeline(
        [
            transport.input(),  # Transport user input
            context_aggregator.user(),
            llm, 
            transport.output(),  # Transport bot output
            transcript.user(),
            transcript.assistant(), 
            context_aggregator.assistant(),
        ]
    )

    # Create pipeline task
    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            allow_interruptions=True,
            enable_metrics=True,
            enable_usage_metrics=True,
            audio_in_sample_rate=SAMPLE_RATE,
            audio_out_sample_rate=SAMPLE_RATE
        ),
    )

    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        """Handles new client connections and initiates conversation."""
        print(f"Client connected")
        await task.queue_frames([context_aggregator.user().get_context_frame()])
        await llm.trigger_assistant_response()

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        """Handles client disconnection and cleanup."""
        print(f"Client disconnected")
        await task.cancel()

    @transcript.event_handler("on_transcript_update")
    async def handle_transcript_update(processor, frame):
        """Logs transcript updates with timestamps."""
        for message in frame.messages:
            print(f"Transcript: [{message.timestamp}] {message.role}: {message.content}")
            
            # If this is a user message, try to enhance it with knowledge base information
            if message.role == "user" and message.content:
                try:
                    # Initialize the knowledge base enhancer with hardcoded KB ID
                    kb_enhancer = KnowledgeBaseEnhancer(kb_id="KCZTEHHZFA")
                    
                    # Retrieve information from the knowledge base
                    kb_info = kb_enhancer.retrieve_from_kb(message.content)
                    
                    if kb_info:
                        print(f"Knowledge base information retrieved: {kb_info[:100]}...")
                except Exception as e:
                    print(f"Error enhancing with knowledge base: {str(e)}")
                    traceback.print_exc()

    runner = PipelineRunner(handle_sigint=False, force_gc=True)
    await runner.run(task)

# Initialize FastAPI application
app = FastAPI()

@app.get('/health')
async def health(request: Request):
    """Health check endpoint."""
    return 'ok'

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint handling client connections.
    Validates API key and sets up the audio processing pipeline.
    """
    protocol = websocket.headers.get('sec-websocket-protocol')
    print('protocol ', protocol)

    await websocket.accept(subprotocol=API_KEY)
    await setup(websocket)

# Configure and start uvicorn server
server = uvicorn.Server(uvicorn.Config(
    app=app,
    host='0.0.0.0',
    port=8000,
    log_level="error"
))

async def serve():
    """Starts the FastAPI server."""
    await server.serve()

# Run the server
asyncio.run(serve())

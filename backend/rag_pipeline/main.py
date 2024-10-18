from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from pydantic import BaseModel
import logging
import json
import utils
import os

from tasks.database import database_connection
from pipeline import Processor

# Load configuration
CONFIG = utils.loadConfigFromEnv()

# Setup logging
if not os.path.exists(CONFIG["CLUSTER_TALK_LOG_PATH"]):
    os.makedirs(CONFIG["CLUSTER_TALK_LOG_PATH"])

logging.basicConfig(
    filename=CONFIG["CLUSTER_TALK_LOG_EXE_PATH"],
    filemode="a",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%d-%m-%y %H:%M:%S",
    level=logging.INFO,
)

# Initialize the models and processor at startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    global processor
    # Database setup and indexing
    os_connection = database_connection.opensearch_connection()
    embedding_model = CONFIG["EMBEDDING_MODEL"]
    embedding_index = CONFIG["EMBEDDING_INDEX"]
    model_configs = json.loads(CONFIG["MODEL_CONFIGS"])

    # Initialize Processor
    processor = Processor(
        opensearch_connection=os_connection,
        embedding_os_index=embedding_index,
        embedding_model=embedding_model,
        model_config=model_configs["mixtral7B"]
    )
    yield
    os_connection.close()

app = FastAPI(lifespan=lifespan)

class QuestionRequest(BaseModel):
    question: str
    question_type: str  # 'corpus-based' or 'document-specific'
    document_ids: list = []  # List of document IDs

class AnswerResponse(BaseModel):
    answer: str
    sources: list

@app.post("/ask", response_model=AnswerResponse)
def ask_question(request: QuestionRequest):
    # Process the request
    try:
        if request.question_type not in ["corpus-based", "document-specific"]:
            raise HTTPException(status_code=400, detail="Invalid question_type. Must be 'corpus-based' or 'document-specific'.")

        # Use the processor to generate the answer
        answer, sources = processor.process_api_request(
            question=request.question,
            question_type=request.question_type,
            document_ids=request.document_ids,
        )

        return AnswerResponse(answer=answer, sources=sources)

    except Exception as e:
        logging.error(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=str(e))
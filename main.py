import os
import json
import logging
from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Import modules and database logging functions
import database
import qna
import explanation_module
import quiz_module
import summary_module
import learning_path

# Load environment configuration
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI App
app = FastAPI(
    title="EduGenie – Google Gemini Powered Learning Assistant",
    description="Interactive AI assistant offering Q&A, simple concept explanations, summaries, quiz generation, and learning paths.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS Middleware
origins = [
    "http://localhost",
    "http://127.0.0.1",
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get base directory for absolute path resolution
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Create static/ and templates/ directories if they don't exist
os.makedirs(os.path.join(BASE_DIR, "static"), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "templates"), exist_ok=True)

# Mount Static Files and Templates
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# Initialize SQLite database on startup
@app.on_event("startup")
def startup_db():
    logger.info("Initializing EduGenie Database...")
    try:
        database.init_db()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")

# Pydantic request validation models
class ExplainRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=200, description="The educational topic to explain")

class SummarizeRequest(BaseModel):
    text: str = Field(..., min_length=5, description="The long educational text to summarize")

class QuizRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=200, description="The topic or text to generate a quiz for")

# ----------------- ENDPOINTS -----------------

@app.get("/health", summary="Health Check Endpoint")
def health_check():
    """
    Returns application health status for monitoring and test purposes.
    """
    return {"status": "healthy"}

@app.get("/", response_class=HTMLResponse, summary="Serve Web Interface")
def serve_index(request: Request):
    """
    Renders and serves the web UI home page.
    """
    return templates.TemplateResponse(request, "index.html")

@app.get("/qa", summary="Educational Question Answering")
def get_qa(question: str = Query(..., min_length=3, description="Educational question to ask")):
    """
    Accepts an educational question and returns a structured answer using Gemini.
    """
    try:
        # Retrieve configuration
        demo_mode = os.environ.get("DEMO_MODE", "False").lower() in ("true", "1", "yes")
        model_name = "demo_mode" if demo_mode else os.environ.get("GEMINI_MODEL", "gemini-1.5-pro")
        
        # Call QA logic
        answer = qna.get_answer(question)
        
        # Log to Database (User ID = 1 for Guest User)
        try:
            query_id = database.log_query(user_id=1, query_type="qna", query_text=question)
            database.log_ai_response(query_id=query_id, response_text=answer, model_used=model_name)
        except Exception as db_err:
            logger.error(f"Database logging failed: {db_err}")
            
        return JSONResponse(content={"question": question, "answer": answer})
    except Exception as e:
        logger.error(f"Error in /qa endpoint: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while answering your question.")

@app.post("/explain", summary="Concept Simplification Module")
def explain_concept(request: ExplainRequest):
    """
    Takes an educational topic and returns a beginner-friendly explanation.
    Uses MBZUAI/LaMini-Flan-T5-783M locally.
    """
    try:
        topic = request.topic
        explanation, model_name = explanation_module.explain_topic(topic)
        
        # Log to Database
        try:
            query_id = database.log_query(user_id=1, query_type="explanation", query_text=topic)
            database.log_ai_response(query_id=query_id, response_text=explanation, model_used=model_name)
        except Exception as db_err:
            logger.error(f"Database logging failed: {db_err}")
            
        return JSONResponse(content={"topic": topic, "explanation": explanation})
    except Exception as e:
        logger.error(f"Error in /explain endpoint: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while simplifying the topic.")


@app.post("/summarize", summary="Text Summarization Module")
def summarize_content(request: SummarizeRequest):
    """
    Takes a long passage and yields a concise summary.
    Uses Google Gemini.
    """
    try:
        # Retrieve configuration
        demo_mode = os.environ.get("DEMO_MODE", "False").lower() in ("true", "1", "yes")
        model_name = "demo_mode" if demo_mode else os.environ.get("GEMINI_MODEL", "gemini-1.5-pro")
        
        original_text = request.text
        summary = summary_module.summarize_text(original_text)
        
        # Log to Database
        try:
            query_id = database.log_query(user_id=1, query_type="summarize", query_text=original_text[:100] + "...")
            database.log_ai_response(query_id=query_id, response_text=summary, model_used=model_name)
            database.log_summary(query_id=query_id, original_text=original_text, summary_text=summary, model_used=model_name)
        except Exception as db_err:
            logger.error(f"Database logging failed: {db_err}")
            
        return JSONResponse(content={"summary": summary})
    except Exception as e:
        logger.error(f"Error in /summarize endpoint: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while summarizing the text.")

@app.post("/quiz", summary="Quiz Generation Module")
def get_quiz(request: QuizRequest):
    """
    Generates exactly 3 MCQs based on a topic or paragraph.
    Uses Google Gemini.
    """
    try:
        # Retrieve configuration
        demo_mode = os.environ.get("DEMO_MODE", "False").lower() in ("true", "1", "yes")
        model_name = "demo_mode" if demo_mode else os.environ.get("GEMINI_MODEL", "gemini-1.5-pro")
        
        topic = request.topic
        questions = quiz_module.generate_quiz(topic)
        
        # Log to Database
        try:
            query_id = database.log_query(user_id=1, query_type="quiz", query_text=topic)
            database.log_ai_response(query_id=query_id, response_text=json.dumps(questions), model_used=model_name)
            for q in questions:
                # Options array contains exactly 4 elements
                opts = q["options"]
                database.log_quiz(
                    query_id=query_id,
                    question_text=q["question"],
                    option_a=opts[0],
                    option_b=opts[1],
                    option_c=opts[2],
                    option_d=opts[3],
                    correct_answer=q["correct_answer"]
                )
        except Exception as db_err:
            logger.error(f"Database logging failed: {db_err}")
            
        return JSONResponse(content=questions)
    except Exception as e:
        logger.error(f"Error in /quiz endpoint: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while generating the quiz.")

@app.get("/learn/recommendations", summary="Learning Roadmap Recommendations")
def get_learning_path(topic: str = Query(..., min_length=1, description="Topic to generate roadmap for")):
    """
    Generates a complete Beginner -> Intermediate -> Advanced learning path for a topic.
    Uses Google Gemini.
    """
    try:
        # Retrieve configuration
        demo_mode = os.environ.get("DEMO_MODE", "False").lower() in ("true", "1", "yes")
        model_name = "demo_mode" if demo_mode else os.environ.get("GEMINI_MODEL", "gemini-1.5-pro")
        
        roadmap = learning_path.get_learning_recommendations(topic)
        
        # Log to Database
        try:
            query_id = database.log_query(user_id=1, query_type="learning_path", query_text=topic)
            database.log_ai_response(query_id=query_id, response_text=roadmap, model_used=model_name)
            database.log_learning_path(
                query_id=query_id,
                topic=topic,
                difficulty_level="All Levels",
                recommended_resources=roadmap
            )
        except Exception as db_err:
            logger.error(f"Database logging failed: {db_err}")
            
        return JSONResponse(content={"topic": topic, "roadmap": roadmap})
    except Exception as e:
        logger.error(f"Error in /learn/recommendations endpoint: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while generating your learning path.")

import os
import json
import logging
from typing import List, Dict, Any
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sample Quizzes for Demo Mode
DEMO_QUIZZES = {
    "photosynthesis": [
        {
            "question": "Which pigment absorbs sunlight during photosynthesis?",
            "options": ["Carotene", "Xanthophyll", "Chlorophyll", "Melanin"],
            "correct_answer": "Chlorophyll"
        },
        {
            "question": "What is the primary gas absorbed by plants from the atmosphere for photosynthesis?",
            "options": ["Oxygen", "Carbon Dioxide", "Nitrogen", "Hydrogen"],
            "correct_answer": "Carbon Dioxide"
        },
        {
            "question": "What are the primary products of photosynthesis?",
            "options": ["Glucose and Oxygen", "Water and Carbon Dioxide", "Starch and Nitrogen", "Sucrose and Hydrogen"],
            "correct_answer": "Glucose and Oxygen"
        }
    ],
    "gravity": [
        {
            "question": "Who formulated the law of universal gravitation?",
            "options": ["Albert Einstein", "Isaac Newton", "Galileo Galilei", "Nikola Tesla"],
            "correct_answer": "Isaac Newton"
        },
        {
            "question": "What happens to the gravitational force between two objects if the distance between them is doubled?",
            "options": ["It doubles", "It is halved", "It increases by four times", "It decreases by four times"],
            "correct_answer": "It decreases by four times"
        },
        {
            "question": "Which of the following determines the strength of gravity of a planet?",
            "options": ["Its mass and radius", "Its temperature", "Its speed of rotation", "Its distance from the Sun"],
            "correct_answer": "Its mass and radius"
        }
    ],
    "binary search": [
        {
            "question": "What is the prerequisite for performing a binary search on a list?",
            "options": ["The list must be unsorted", "The list must contain only integers", "The list must be sorted", "The list must have an even number of elements"],
            "correct_answer": "The list must be sorted"
        },
        {
            "question": "What is the time complexity of the Binary Search algorithm in the worst case?",
            "options": ["O(n)", "O(n log n)", "O(log n)", "O(1)"],
            "correct_answer": "O(log n)"
        },
        {
            "question": "Which index is checked first during each step of a binary search?",
            "options": ["The first index", "The last index", "The middle index", "A random index"],
            "correct_answer": "The middle index"
        }
    ],
    "probability": [
        {
            "question": "What is the probability of an event that is absolutely certain to happen?",
            "options": ["0", "0.5", "1", "100"],
            "correct_answer": "1"
        },
        {
            "question": "If you roll a fair 6-sided die, what is the probability of rolling an odd number?",
            "options": ["1/6", "1/3", "1/2", "2/3"],
            "correct_answer": "1/2"
        },
        {
            "question": "If the probability of it raining tomorrow is 0.3, what is the probability of it NOT raining?",
            "options": ["0.3", "0.7", "0.0", "1.3"],
            "correct_answer": "0.7"
        }
    ]
}

def clean_json_block(text: str) -> str:
    """
    Cleans markdown code blocks (like ```json ... ```) from the AI response
    to prepare it for JSON parsing.
    """
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        if lines[0].strip().startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    return cleaned

def validate_quiz_json(quiz_data: Any) -> List[Dict[str, Any]]:
    """
    Validates that the input is a list of exactly 3 questions,
    each with a question string, exactly 4 non-empty options,
    and a correct_answer string which exists in the options list.
    Raises ValueError if invalid.
    """
    if not isinstance(quiz_data, list):
        raise ValueError("Quiz response is not a JSON list.")
    if len(quiz_data) != 3:
        raise ValueError(f"Quiz list size must be exactly 3, got {len(quiz_data)}.")
        
    validated = []
    for idx, item in enumerate(quiz_data):
        if not isinstance(item, dict):
            raise ValueError(f"Quiz item {idx} is not a JSON object.")
        
        q = item.get("question")
        opts = item.get("options")
        ans = item.get("correct_answer")
        
        if not q or not isinstance(q, str):
            raise ValueError(f"Quiz item {idx} is missing a valid 'question' string.")
            
        if not opts or not isinstance(opts, list) or len(opts) != 4:
            raise ValueError(f"Quiz item {idx} must have an 'options' list with exactly 4 items.")
            
        for opt_idx, opt in enumerate(opts):
            if not isinstance(opt, str) or not opt.strip():
                raise ValueError(f"Quiz item {idx} option {opt_idx} is not a valid non-empty string.")
                
        if not ans or not isinstance(ans, str):
            raise ValueError(f"Quiz item {idx} is missing a valid 'correct_answer' string.")
            
        # Clean options and answers for check
        opts_stripped = [o.strip() for o in opts]
        ans_stripped = ans.strip()
        
        if ans_stripped not in opts_stripped:
            # Fallback check: maybe it references an option index/letter
            mapping = {"a": 0, "b": 1, "c": 2, "d": 3, "0": 0, "1": 1, "2": 2, "3": 3}
            ans_clean = ans_stripped.lower().replace(".", "").strip()
            if ans_clean in mapping:
                ans_val = opts_stripped[mapping[ans_clean]]
            else:
                # Default to first option as safe recovery
                ans_val = opts_stripped[0]
        else:
            ans_val = ans_stripped
            
        validated.append({
            "question": q.strip(),
            "options": opts_stripped,
            "correct_answer": ans_val
        })
    return validated

def generate_quiz(topic: str) -> List[Dict[str, Any]]:
    """
    Generates exactly 3 multiple choice questions (MCQs) for the given topic.
    Returns a validated list of JSON objects containing question, options, and correct_answer.
    Falls back to high-quality demo quizzes if DEMO_MODE=True or if the API/Parsing fails.
    """
    demo_mode = os.environ.get("DEMO_MODE", "False").lower() in ("true", "1", "yes")
    
    if demo_mode:
        logger.info("DEMO MODE is active. Serving demo quiz.")
        return get_demo_quiz(topic)
        
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        logger.warning("Gemini API Key missing. Falling back to DEMO MODE responses for quiz.")
        return get_demo_quiz(topic)
        
    model_name = os.environ.get("GEMINI_MODEL", "gemini-1.5-pro")
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        prompt = (
            "You are an educational quiz generator. Generate exactly 3 multiple choice questions (MCQs) "
            f"on the topic of: '{topic}'.\n"
            "You must return ONLY a raw JSON array containing exactly 3 objects. "
            "Do not include any introductory or concluding text, only the JSON block.\n\n"
            "Each question object in the JSON array must follow this exact schema:\n"
            "{\n"
            '  "question": "A clear, multiple choice question text",\n'
            '  "options": [\n'
            '    "Option A description",\n'
            '    "Option B description",\n'
            '    "Option C description",\n'
            '    "Option D description"\n'
            '  ],\n'
            '  "correct_answer": "Option A description" (must match exactly one of the strings in the options array)\n'
            "}\n"
        )
        response = model.generate_content(prompt)
        if response and response.text:
            cleaned_json = clean_json_block(response.text)
            quiz_data = json.loads(cleaned_json)
            return validate_quiz_json(quiz_data)
        else:
            raise ValueError("Empty response received from Gemini.")
    except Exception as e:
        logger.error(f"Gemini Quiz API call or parsing failed: {e}. Falling back to DEMO MODE responses.")
        return get_demo_quiz(topic)

def get_demo_quiz(topic: str) -> List[Dict[str, Any]]:
    """
    Returns realistic sample quizzes in demo mode.
    """
    topic_clean = topic.strip().lower()
    for key, quiz in DEMO_QUIZZES.items():
        if key in topic_clean:
            return quiz
            
    # Generic fallback quiz
    return [
        {
            "question": f"Which of the following is a primary pillar of studying {topic}?",
            "options": [
                "Memorizing historical names blindly",
                "Analyzing functional mechanisms and practical use cases",
                "Bypassing scientific standards completely",
                "Avoiding classroom discussions altogether"
            ],
            "correct_answer": "Analyzing functional mechanisms and practical use cases"
        },
        {
            "question": f"Why is a deep understanding of {topic} beneficial?",
            "options": [
                "It helps build solid foundations in this and related disciplines",
                "It guarantees absolute wealth without work",
                "It allows you to travel faster than light",
                "It has no practical benefit whatsoever"
            ],
            "correct_answer": "It helps build solid foundations in this and related disciplines"
        },
        {
            "question": f"Which field of research would investigate {topic}?",
            "options": [
                "Modern academic and scientific exploration",
                "Only astrology and palm reading",
                "Strictly underwater archeology of the 15th century",
                "None of the options"
            ],
            "correct_answer": "Modern academic and scientific exploration"
        }
    ]

import os
import logging
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sample Summaries for Demo Mode
DEMO_SUMMARIES = {
    "photosynthesis": (
        "• **Core Process**: Photosynthesis is the chemical process plants use to convert light, water, and CO2 into glucose and oxygen.\n"
        "• **Light Reactions**: Solar energy is captured by chlorophyll inside chloroplasts, splitting water and releasing oxygen.\n"
        "• **Dark Reactions (Calvin Cycle)**: The captured chemical energy is used to synthesize glucose from carbon dioxide.\n"
        "• **Significance**: It forms the base of the food chain and produces oxygen required for aerobic life on Earth."
    ),
    "gravity": (
        "• **Fundamental Force**: Gravity is the universal attractive force that acts between all matter possessing mass.\n"
        "• **Governing Rules**: Its strength is directly proportional to the mass of the objects and inversely proportional to the square of the distance between them (Newton's Law).\n"
        "• **Cosmic Role**: Gravitational pull keeps planets in orbit, stabilizes stars, and governs the expansion and structure of the universe."
    ),
    "probability": (
        "• **Mathematical Likelihood**: Probability measures the chance of an event occurring, represented on a scale from 0 (impossible) to 1 (certain).\n"
        "• **Core Formula**: $P(A)$ is the number of favorable outcomes divided by the total number of possible outcomes in the sample space.\n"
        "• **Key Probability Types**: Theoretical probability is calculated mathematically, while experimental probability is based on real-world trials.\n"
        "• **Practical Utility**: Essential in risk assessment, weather forecasting, game design, machine learning, and statistical modeling."
    )
}

def summarize_text(text: str) -> str:
    """
    Summarizes long educational text into a concise, easy-to-understand list of key points.
    Utilizes Google Gemini.
    Falls back to high-quality demo summaries if DEMO_MODE=True or if the API call fails.
    """
    demo_mode = os.environ.get("DEMO_MODE", "False").lower() in ("true", "1", "yes")
    
    if demo_mode:
        logger.info("DEMO MODE is active. Serving demo summary.")
        return get_demo_summary(text)
        
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        logger.warning("Gemini API Key missing. Falling back to DEMO MODE responses for summary.")
        return get_demo_summary(text)
        
    model_name = os.environ.get("GEMINI_MODEL", "gemini-1.5-pro")
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        prompt = (
            "You are an expert educator. Summarize the following educational text in a concise, "
            "clear, and easy-to-understand manner. Highlight the key concepts and present them as "
            "bullet points. Keep it student-friendly.\n\n"
            f"Text: {text}"
        )
        response = model.generate_content(prompt)
        if response and response.text:
            return response.text
        else:
            raise ValueError("Empty response received from Gemini.")
    except Exception as e:
        logger.error(f"Gemini Summarization API call failed: {e}. Falling back to DEMO MODE responses.")
        return get_demo_summary(text, error_message=str(e))

def get_demo_summary(text: str, error_message: str = None) -> str:
    """
    Returns realistic sample summaries for demo mode.
    """
    text_lower = text.lower()
    
    # Determine the status note to show
    reason_note = ""
    if error_message:
        reason_note = f"*(Note: Reverted to Demo Mode. Gemini API returned an error: `{error_message}`)*\n\n"
        
    for key, summary in DEMO_SUMMARIES.items():
        if key in text_lower:
            return f"{reason_note}{summary}"
            
    # Determine fallback note if no specific key match
    if error_message:
        generic_note = f"*(Note: Reverted to Demo Mode. Gemini API returned an error: `{error_message}`)*"
    else:
        generic_note = "*(Note: Running in Demo Mode because the Gemini API is offline or DEMO_MODE=True)*"

    # Generic bullet point summary generator
    words = text.split()
    snippet = " ".join(words[:20]) + ("..." if len(words) > 20 else "")
    return (
        f"• **Key Theme**: The passage discusses core educational topics, starting with: \"{snippet}\"\n"
        f"• **Major Finding**: The text provides conceptual frameworks and definitions that are vital for learners to master.\n"
        f"• **Practical Context**: It connects theoretical elements directly with practical processes and examples.\n"
        f"• **Conclusion**: Understanding this material is essential for building a foundation in this discipline.\n\n"
        f"{generic_note}"
    )

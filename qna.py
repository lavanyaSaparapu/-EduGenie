import os
import logging
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEMO_ANSWERS = {
    "photosynthesis": (
        "### Photosynthesis Explained\n\n"
        "**Photosynthesis** is the process by which green plants, algae, and some bacteria convert light energy (usually from the Sun) into chemical energy (glucose) that fuels their activities. \n\n"
        "#### The Chemical Equation:\n"
        "$$6\\text{CO}_2 + 6\\text{H}_2\\text{O} + \\text{Light Energy} \\rightarrow \\text{C}_6\\text{H}_{12}\\text{O}_6 + 6\\text{O}_2$$\n"
        "(Carbon Dioxide + Water + Sunlight $\\rightarrow$ Glucose + Oxygen)\n\n"
        "#### How it Works in 3 Simple Steps:\n"
        "1. **Light Capture**: Chlorophyll (the green pigment inside plant cells' chloroplasts) absorbs sunlight.\n"
        "2. **Water Splitting**: The plant absorbs water through its roots. Sunlight splits water molecules into hydrogen and oxygen. The oxygen is released as a byproduct into the atmosphere (which is what we breathe!).\n"
        "3. **Carbon Dioxide Conversion**: The plant takes carbon dioxide from the air and combines it with hydrogen to create glucose, which serves as food for the plant and helps it grow."
    ),
    "gravity": (
        "### Gravity Explained\n\n"
        "**Gravity** is an invisible force that pulls objects toward each other. It is what keeps your feet on the ground and what makes objects fall when you drop them.\n\n"
        "#### Key Concepts:\n"
        "- **Mass**: Anything that has mass has gravity. The more mass an object has (like the Earth), the stronger its gravitational pull.\n"
        "- **Distance**: The closer you are to an object, the stronger its gravity. As you move farther away, the pull gets weaker.\n\n"
        "#### Fun Fact:\n"
        "You actually have your own gravitational pull! However, because your mass is very small compared to the Earth, your gravity is too weak to attract other objects."
    ),
    "binary search": (
        "### Binary Search Algorithm\n\n"
        "**Binary Search** is an efficient algorithm for finding an item from a sorted list of items. It works by repeatedly dividing in half the portion of the list that could contain the item, until you've narrowed down the possible locations to just one.\n\n"
        "#### Visual Explanation:\n"
        "If you are searching for a word in a physical dictionary, you don't read page by page from the beginning. Instead, you open the book in the middle. If the target word comes alphabetically after the middle page, you ignore the first half of the book and repeat the search on the second half.\n\n"
        "#### Complexity:\n"
        "- **Time Complexity**: $O(\\log n)$ - extremely fast, even for billions of elements.\n"
        "- **Space Complexity**: $O(1)$ for iterative search."
    ),
    "probability": (
        "### Probability Explained\n\n"
        "**Probability** is the mathematical study of chance and uncertainty. It measures how likely an event is to occur, represented as a value between **0** (impossible) and **1** (absolutely certain).\n\n"
        "#### The Core Formula:\n"
        "For an event $A$, the probability $P(A)$ is defined as:\n"
        "$$P(A) = \\frac{\\text{Number of Favorable Outcomes}}{\\text{Total Number of Possible Outcomes}}$$\n\n"
        "#### Key Terminology:\n"
        "- **Experiment**: A repeatable process that produces outcomes (e.g., rolling a die).\n"
        "- **Sample Space ($S$)**: The set of all possible outcomes. For a 6-sided die, $S = \\{1, 2, 3, 4, 5, 6\\}$.\n"
        "- **Event ($A$)**: The specific outcome(s) you are interested in. For example, rolling an even number: $A = \\{2, 4, 6\\}$.\n"
        "- **Complement ($A'$)**: The event not happening: $P(A') = 1 - P(A)$.\n\n"
        "#### Real-World Example:\n"
        "If you roll a standard 6-sided die, the probability of rolling a number greater than 4 (meaning a 5 or 6) is:\n"
        "$$P(>4) = \\frac{2}{6} = \\frac{1}{3} \\approx 33.3\\%$$"
    )
}

def get_answer(question: str) -> str:
    """
    Retrieves a student-friendly educational answer for the given question.
    Connects to Google Gemini model configured in GEMINI_MODEL.
    Falls back to high-quality demo answers if DEMO_MODE=True or if the API call fails.
    """
    demo_mode = os.environ.get("DEMO_MODE", "False").lower() in ("true", "1", "yes")
    
    if demo_mode:
        logger.info("DEMO MODE is active. Serving demo response for Q&A.")
        return get_demo_answer(question)
        
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        logger.warning("Gemini API Key missing. Falling back to DEMO MODE responses for Q&A.")
        return get_demo_answer(question)
        
    model_name = os.environ.get("GEMINI_MODEL", "gemini-1.5-pro")
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        prompt = (
            "You are a helpful, professional, and student-friendly educational assistant. "
            "Explain the following concept or answer the student's question clearly, "
            "providing definitions, structural breakdowns, formatting where useful (e.g. markdown headers, lists), "
            "and real-world examples. Ensure it is easy to understand.\n\n"
            f"Question: {question}"
        )
        response = model.generate_content(prompt)
        if response and response.text:
            return response.text
        else:
            raise ValueError("Empty response received from Gemini.")
    except Exception as e:
        logger.error(f"Gemini Q&A API call failed: {e}. Falling back to DEMO MODE responses.")
        return get_demo_answer(question, error_message=str(e))

def get_demo_answer(question: str, error_message: str = None) -> str:
    """
    Returns realistic educational sample answers for demo mode.
    """
    q_lower = question.lower()
    
    # Determine the status note to show
    reason_note = ""
    if error_message:
        reason_note = f"*(Note: Reverted to Demo Mode. Gemini API returned an error: `{error_message}`)*\n\n"
        
    for key, answer in DEMO_ANSWERS.items():
        if key in q_lower:
            return f"{reason_note}{answer}"
            
    # Generic note for fallback
    if error_message:
        generic_note = f"*(Note: Reverted to Demo Mode. Gemini API returned an error: `{error_message}`)*"
    else:
        generic_note = (
            "*(Note: Running in Demo Mode because DEMO_MODE=True)*\n\n"
            "To get a customized explanation directly from Gemini, make sure to add your `GEMINI_API_KEY` in the `.env` file and set `DEMO_MODE=False`."
        )

    # Generic educational answer
    return (
        f"### Explanation for: '{question}'\n\n"
        f"{generic_note}\n\n"
        "This concept is highly relevant to modern academics. To understand it fully, we can analyze it through these three dimensions:\n\n"
        "1. **Core Concept**: What is the basic idea? It refers to the fundamental principles that govern this topic.\n"
        "2. **Functional Mechanism**: How does it work? It operates by combining structural inputs with processes to achieve outputs.\n"
        "3. **Practical Examples**: In real life, we see this in action across scientific models, technological solutions, and everyday applications."
    )

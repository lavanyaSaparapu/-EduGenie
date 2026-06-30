import os
import logging
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sample Learning Paths for Demo Mode
DEMO_PATHWAYS = {
    "photosynthesis": (
        "### 🌿 Learning Roadmap: Photosynthesis\n\n"
        "#### 1. Beginner Level\n"
        "- **Key Concepts**: Basic inputs (Sunlight, Water, Carbon Dioxide), the green pigment Chlorophyll, and the releasing of Oxygen.\n"
        "- **Recommended Resources**:\n"
        "  - 🎥 *Crash Course Kids: Photosynthesis* (Free educational YouTube video explaining plant food factories).\n"
        "  - 📖 *DK Eyewitness: Plant* (Highly visual and accessible guidebook for starting biology students).\n\n"
        "#### 2. Intermediate Level\n"
        "- **Key Concepts**: Chloroplast anatomy (Thylakoids and Stroma), Light-Dependent reactions, Light-Independent reactions (Calvin Cycle), and Stomata functions.\n"
        "- **Recommended Resources**:\n"
        "  - 📖 *Khan Academy: Cellular Energetics* (Online unit detailing photosynthesis chemical steps).\n"
        "  - 🧪 *Virtual Lab: Photosynthesis Simulation* (Interactive online workspace showing how light color/intensity affects oxygen bubble release).\n\n"
        "#### 3. Advanced Level\n"
        "- **Key Concepts**: Photosynthetic Electron Transport Chain, ATP Synthase mechanics, Photorespiration, and differences in C3, C4, and CAM plants.\n"
        "- **Recommended Resources**:\n"
        "  - 📘 *Campbell Biology - Chapter 10* (The gold-standard reference textbook chapter for biology majors).\n"
        "  - 🔬 *MIT OpenCourseWare: General Biology* (Free lecture videos and exam resources on plant biochemistry)."
    ),
    "gravity": (
        "### 🌌 Learning Roadmap: Gravity & Gravitation\n\n"
        "#### 1. Beginner Level\n"
        "- **Key Concepts**: Basic definition of gravity, Mass vs. Weight, Falling objects, and why things float in space.\n"
        "- **Recommended Resources**:\n"
        "  - 🎥 *NASA Space Place: What is Gravity?* (Accessible articles and short animations).\n"
        "  - 📖 *Gravity* by Jason Chin (An award-winning illustrated guide to how gravity holds the world together).\n\n"
        "#### 2. Intermediate Level\n"
        "- **Key Concepts**: Newton's Law of Universal Gravitation ($F = G \\frac{m_1 m_2}{r^2}$), Acceleration due to gravity ($g = 9.8 \\text{ m/s}^2$), Orbit mechanics, and Escape Velocity.\n"
        "- **Recommended Resources**:\n"
        "  - 📖 *The Physics Classroom: Circular Motion and Gravitation* (Clear conceptual summaries and practice problem solvers).\n"
        "  - 🎮 *PhET Interactive Simulations: Gravity Force Lab* (Interactive slider tools to visualize mass and distance relationships).\n\n"
        "#### 3. Advanced Level\n"
        "- **Key Concepts**: Einstein's General Theory of Relativity (Spacetime curvature), Gravitational Lensing, Black holes, and Gravitational Waves.\n"
        "- **Recommended Resources**:\n"
        "  - 📘 *Spacetime and Geometry: An Introduction to General Relativity* by Sean Carroll (Undergraduate/graduate level textbook).\n"
        "  - 🎥 *Stanford University: General Relativity* by Prof. Leonard Susskind (Available on YouTube)."
    ),
    "binary search": (
        "### 💻 Learning Roadmap: Binary Search\n\n"
        "#### 1. Beginner Level\n"
        "- **Key Concepts**: Sorted lists necessity, High/Low/Mid boundaries, Divide and Conquer approach, and visual dictionary game analogy.\n"
        "- **Recommended Resources**:\n"
        "  - 🎥 *CS50: Binary Search* (Harvard's intro lecture clip with physical phonebook ripping demo).\n"
        "  - 🎮 *VisuAlgo: Binary Search Tree* (Interactive tool displaying search progressions visually).\n\n"
        "#### 2. Intermediate Level\n"
        "- **Key Concepts**: Iterative vs. Recursive implementations, Boundary index updates (preventing integer overflow `mid = low + (high - low) / 2`), and Time Complexity analysis ($O(\\log n)$).\n"
        "- **Recommended Resources**:\n"
        "  - 📖 *Introduction to Algorithms (CLRS) - Binary Search Section* (Rigorous proofing and code structure).\n"
        "  - 💻 *LeetCode / HackerRank Search Problems* (Solving easy/medium challenges like 'Search Insert Position').\n\n"
        "#### 3. Advanced Level\n"
        "- **Key Concepts**: Binary search on answer space (optimizing search variables), checking helper functions (`canFeasible()`), and ternary search for unimodal functions.\n"
        "- **Recommended Resources**:\n"
        "  - 📘 *Competitive Programmer's Handbook - Chapter 3* (Short, targeted explanations of advanced search applications).\n"
        "  - 🏆 *TopCoder / Codeforces Binary Search tutorials* (Comprehensive guides to binary searching on complex monotonic functions)."
    ),
    "probability": (
        "### 📊 Learning Roadmap: Probability & Statistics\n\n"
        "#### 1. Beginner Level\n"
        "- **Key Concepts**: Simple events, Sample Space, outcomes, coin flips, rolling dice, and basic fractions/percentages representing likelihood.\n"
        "- **Recommended Resources**:\n"
        "  - 🎥 *Math Antics - Basic Probability* (Extremely clear, visual introductory video).\n"
        "  - 📖 *Khan Academy: Basic Theoretical Probability* (Practice sets and short interactive modules).\n\n"
        "#### 2. Intermediate Level\n"
        "- **Key Concepts**: Independent vs. Dependent events, Conditional Probability, Bayes' Theorem, Venn Diagrams, and tree diagrams.\n"
        "- **Recommended Resources**:\n"
        "  - 📖 *OpenStax: Introductory Statistics* (Free high-quality open-source textbook chapters on probability rules).\n"
        "  - 🧪 *PhET Probability Simulation* (Interactive marble jar and coin toss simulators online).\n\n"
        "#### 3. Advanced Level\n"
        "- **Key Concepts**: Probability Distributions (Normal, Binomial, Poisson), Random Variables, Expected Value, Central Limit Theorem, and Markov Chains.\n"
        "- **Recommended Resources**:\n"
        "  - 📘 *Introduction to Probability* by Joseph K. Blitzstein and Jessica Hwang (Harvard introductory textbook).\n"
        "  - 🎥 *MIT 18.05 Introduction to Probability and Statistics* (Lecture series and course materials available via MIT OCW)."
    )
}

def get_learning_recommendations(topic: str) -> str:
    """
    Generates a structured learning path/roadmap for a given educational topic.
    Includes Beginner, Intermediate, and Advanced stages, each with concepts and resources.
    Utilizes Google Gemini.
    Falls back to high-quality demo paths if DEMO_MODE=True or if the API fails.
    """
    demo_mode = os.environ.get("DEMO_MODE", "False").lower() in ("true", "1", "yes")
    
    if demo_mode:
        logger.info("DEMO MODE is active. Serving demo learning roadmap.")
        return get_demo_roadmap(topic)
        
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        logger.warning("Gemini API Key missing. Falling back to DEMO MODE responses for learning path.")
        return get_demo_roadmap(topic)
        
    model_name = os.environ.get("GEMINI_MODEL", "gemini-1.5-pro")
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        prompt = (
            "You are a professional educational curriculum designer. Create a structured learning roadmap "
            f"for the topic: '{topic}'.\n"
            "Format the roadmap using Markdown headers and lists. The roadmap MUST contain three distinct levels:\n\n"
            "1. **Beginner Level**\n"
            "   - Core concepts to study\n"
            "   - Specific online or offline resources (books, videos, courses)\n\n"
            "2. **Intermediate Level**\n"
            "   - Core concepts to study\n"
            "   - Specific online or offline resources\n\n"
            "3. **Advanced Level**\n"
            "   - Core concepts to study\n"
            "   - Specific online or offline resources\n\n"
            "Make it comprehensive, engaging, and easy to read."
        )
        response = model.generate_content(prompt)
        if response and response.text:
            return response.text
        else:
            raise ValueError("Empty response received from Gemini during roadmap generation.")
    except Exception as e:
        logger.error(f"Gemini Learning Path API call failed: {e}. Falling back to DEMO MODE responses.")
        return get_demo_roadmap(topic, error_message=str(e))

def get_demo_roadmap(topic: str, error_message: str = None) -> str:
    """
    Returns realistic sample roadmaps in demo mode.
    """
    topic_clean = topic.strip().lower()
    
    # Determine the status note to show
    reason_note = ""
    if error_message:
        reason_note = f"*(Note: Reverted to Demo Mode. Gemini API returned an error: `{error_message}`)*\n\n"
        
    for key, path in DEMO_PATHWAYS.items():
        if key in topic_clean:
            return f"{reason_note}{path}"
            
    # Determine fallback note if no specific key match
    if error_message:
        generic_note = f"*(Note: Reverted to Demo Mode. Gemini API returned an error: `{error_message}`)*"
    else:
        generic_note = "*(Note: Running in Demo Mode because the Gemini API is currently unavailable or DEMO_MODE=True)*"

    # Generic fallback learning path
    return (
        f"### 📚 Learning Roadmap: {topic}\n\n"
        f"{generic_note}\n\n"
        "Here is a recommended educational sequence to master this topic:\n\n"
        "#### 1. Beginner Level\n"
        f"- **Key Concepts**: Fundamental definitions, basic components of {topic}, and historical background.\n"
        "- **Recommended Resources**:\n"
        "  - 🎥 *Introductory YouTube tutorials* (Search for visual overviews of the concept).\n"
        f"  - 📖 *Introductory school textbooks* (Review early chapters on {topic}).\n\n"
        "#### 2. Intermediate Level\n"
        f"- **Key Concepts**: Inner workings, mathematical models or structures, and how {topic} connects to other systems.\n"
        "- **Recommended Resources**:\n"
        "  - 💻 *Interactive online courses* (Check Coursera, edX, or Khan Academy).\n"
        "  - 🧪 *Virtual labs and simulators* (Practice manipulating variable parameters to see results).\n\n"
        "#### 3. Advanced Level\n"
        f"- **Key Concepts**: Theoretical boundary limits, recent scientific research developments, and specialized industry applications of {topic}.\n"
        "- **Recommended Resources**:\n"
        "  - 📘 *Advanced college textbooks and research papers* (Look up papers on Google Scholar).\n"
        "  - 🔬 *MIT OpenCourseWare / Stanford Online* lectures on specialized disciplines."
    )

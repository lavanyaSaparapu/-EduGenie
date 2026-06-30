import os
import logging
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cache variables
_pipe = None

DEMO_EXPLANATIONS = {
    "photosynthesis": (
        "Photosynthesis is how plants make their own food! Think of a plant as a tiny food factory. "
        "It takes in water from the ground, carbon dioxide from the air, and sunlight from the sky. "
        "Inside its green leaves, it uses the sunlight's energy to mix the water and carbon dioxide together. "
        "This makes sugar (which is the plant's food) and oxygen (which plants release into the air for us to breathe). "
        "So, plants use sun, air, and water to grow and keep us alive!"
    ),
    "gravity": (
        "Gravity is like an invisible magnet that pulls things together. Everything that has weight (mass) has gravity. "
        "Because the Earth is so huge, it has a lot of gravity. This gravity pulls on you and everything around you, "
        "keeping your feet on the ground and keeping the air we breathe from floating off into space! "
        "When you jump, it's Earth's gravity that pulls you back down. The closer you are to something, the stronger the pull."
    ),
    "binary search": (
        "Binary Search is a super fast way to find something in a sorted list. "
        "Imagine you are guessing a number between 1 and 100, and I tell you if your guess is too high or too low. "
        "Instead of guessing 1, 2, 3, 4, etc. (which could take 100 tries!), you guess 50. If I say 'too high', you know the number is between 1 and 49. "
        "You just cut your choices in half! Next, you guess 25. By always guessing the middle number, you find the answer very quickly. "
        "That's how binary search works in computer programs!"
    ),
    "probability": (
        "Probability is just a way of measuring how likely something is to happen! "
        "Think of it like a weather report: if the meteorologist says there is a 90% chance of rain, "
        "it means it's very likely to rain. If they say 10%, it's probably going to stay dry. "
        "We use numbers between 0 and 1 to talk about probability. A probability of 0 means something is "
        "completely impossible (like a pig flying on its own), while a 1 means it is absolutely guaranteed "
        "to happen (like the sun rising tomorrow). "
        "For example, if you flip a coin, there are only two possibilities: heads or tails. "
        "Since both are equally likely, the probability of landing on heads is 1 out of 2, or 50%!"
    )
}

def get_explanation_pipeline(local_files_only: bool = True):
    """
    Lazily loads the MBZUAI/LaMini-Flan-T5-783M model and caches it in memory.
    Supports GPU (CUDA) execution when available, and falls back to CPU.
    """
    global _pipe
    if _pipe is None:
        # Import transformers inside the function for lazy loading
        from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
        import torch
        
        model_name = "MBZUAI/LaMini-Flan-T5-783M"
        # Determine device
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Initializing model {model_name} on device: {device} (local_files_only={local_files_only})")
        
        try:
            tokenizer = AutoTokenizer.from_pretrained(model_name, local_files_only=local_files_only)
            # Load model with mixed precision on GPU, standard precision on CPU
            model = AutoModelForSeq2SeqLM.from_pretrained(
                model_name,
                torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                device_map="auto" if device == "cuda" else None,
                local_files_only=local_files_only
            )
            
            _pipe = pipeline(
                "text2text-generation",
                model=model,
                tokenizer=tokenizer,
                max_length=512,
                do_sample=True,
                temperature=0.7,
                top_p=0.9
            )
            logger.info("Local HuggingFace model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load model {model_name} from HuggingFace: {e}")
            raise e
            
    return _pipe


def explain_topic(topic: str) -> tuple[str, str]:
    """
    Explains a complex concept in simple, beginner-friendly language.
    Attempts to use Google Gemini first if an API key is present.
    If the API is not configured or fails, falls back to the local LaMini-Flan-T5-783M model,
    and finally back to demo mode fallback explanations.
    """
    demo_mode = os.environ.get("DEMO_MODE", "False").lower() in ("true", "1", "yes")
    
    if demo_mode:
        logger.info("DEMO MODE is active. Serving demo explanation.")
        return get_demo_explanation(topic), "demo_mode"
        
    # Attempt using Google Gemini first
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if api_key:
        model_name = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
        try:
            logger.info(f"Generating explanation using Gemini ({model_name})...")
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(model_name)
            prompt = (
                "You are a friendly, encouraging, and clear academic tutor. "
                f"Explain the educational topic of '{topic}' in simple language suitable for a beginner or a child. "
                "Use bold text for key terms, lists, and an easy real-world analogy to make it easy to understand."
            )
            response = model.generate_content(prompt)
            if response and response.text:
                return response.text, model_name
            else:
                raise ValueError("Empty response received from Gemini.")
        except Exception as gemini_err:
            logger.warning(f"Gemini explanation generation failed: {gemini_err}. Trying local model...")

    # Fallback to local HuggingFace T5 model
    try:
        logger.info("Attempting local HuggingFace T5 explanation...")
        allow_download = os.environ.get("ALLOW_MODEL_DOWNLOAD", "False").lower() in ("true", "1", "yes")
        pipe = get_explanation_pipeline(local_files_only=not allow_download)
        prompt = f"Explain the topic of '{topic}' in simple language suitable for a beginner or a child."
        res = pipe(prompt)
        if res and len(res) > 0:
            return res[0]["generated_text"], "MBZUAI/LaMini-Flan-T5-783M"
        else:
            raise ValueError("No output generated by local model pipeline.")
    except Exception as local_err:
        logger.error(f"Local model explanation failed: {local_err}. Falling back to DEMO MODE explanation.")
        err_msg = str(local_err) if not api_key else f"Gemini failed & local model failed: {local_err}"
        return get_demo_explanation(topic, error_message=err_msg), "demo_mode"


def get_demo_explanation(topic: str, error_message: str = None) -> str:
    """
    Generates a beginner-friendly sample explanation for a topic in demo mode.
    """
    topic_clean = topic.strip().lower()
    
    # Determine the status note to show
    reason_note = ""
    if error_message:
        reason_note = f"*(Note: Reverted to Demo Mode. Local Model/API returned an error: `{error_message}`)*\n\n"
        
    for key, explanation in DEMO_EXPLANATIONS.items():
        if key in topic_clean:
            return f"{reason_note}{explanation}"
            
    # If not a predefined key, attempt to generate using local model
    if not error_message:
        try:
            pipe = get_explanation_pipeline(local_files_only=True)
            prompt = f"Explain the topic of '{topic}' in simple language suitable for a beginner or a child."
            res = pipe(prompt)
            if res and len(res) > 0:
                custom_explanation = res[0]["generated_text"]
                note = "*(Note: Generated using local MBZUAI/LaMini-Flan-T5-783M model)*"
                return f"{custom_explanation}\n\n{note}"
        except Exception as local_err:
            logger.warning(f"Local model generation failed: {local_err}. Using generic template.")
            
    # Determine fallback note if no specific key match
    if error_message:
        generic_note = f"*(Note: Reverted to Demo Mode. Local Model/API returned an error: `{error_message}`)*"
    else:
        generic_note = "*(Note: Running in Demo Mode. Connect an API Key or download the model weights to get custom explanations.)*"

    # Generic simple explanation generator
    return (
        f"Let's explain **{topic}** in a very simple way!\n\n"
        f"Imagine you are explaining '{topic}' to a friend who has never heard of it before. "
        "Here are the most important things to know:\n\n"
        f"- **What is it?** {topic} is a concept we use to describe a specific pattern or idea in our world.\n"
        "- **Why does it matter?** Without it, we wouldn't be able to solve certain problems or understand how things fit together.\n"
        "- **An easy example**: Think of it like building with blocks. You need a solid base before you can build a tall tower. "
        f"In the same way, {topic} serves as a building block for advanced learning!\n\n"
        f"{generic_note}"
    )



from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from google import genai
from google.genai import types
import os
import json


class LLMGenerationController:

    def generate_action_areas(self, data):
        try:
            system_prompt = """
    You are an Educational Feedback Analysis Expert.

    Your task is to analyze multiple feedback comments and generate a short, clear, and structured summary.

    GOAL:
    - Identify key strengths.
    - Identify key improvement areas.
    - Group similar feedback.
    - Keep all points short, simple, and easy to understand.
    - Avoid repetition.

    OUTPUT RULES (STRICT):

    Return ONLY valid JSON.
    Do NOT add explanations.
    Do NOT use markdown.
    Do NOT add extra text.

    JSON STRUCTURE:

    {
    "immediate_action_summary": "short 3-4 sentence paragraph",
    "continue": ["point 1", "point 2", "point 3"],
    "start": ["point 1", "point 2", "point 3"],
    "stop": ["point 1", "point 2", "point 3"]
    }

    CONTENT RULES:

    Immediate Action Summary:
    - 3–4 short sentences.
    - Focus only on the most important improvement themes.
    - Keep language simple and direct.

    Continue:
    - Maximum 3 points.
    - Short (1 sentence each).
    - Only clear strengths.

    Start:
    - Maximum 3 points.
    - Short and actionable.
    - Clear improvement steps.

    Stop:
    - Maximum 3 points.
    - Short and direct.
    - Only clearly criticized practices.

    GENERAL RULES:
    - Combine similar comments into one point.
    - Prioritize frequently mentioned themes.
    - No emotional language.
    - No complex wording.
    - Each bullet must be concise and easy to understand.
    - If no data exists for a section, write:
    "No significant concerns identified in this area."

    IMPORTANT:
    Do not exceed 3 points per section.
    Keep all points short and clear.
    """
            feedback_schema = {
                "type": "object",
                "properties": {
                    
                    "continue": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Strengths that should be continued."
                    },
                    "start": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "New actions or improvements to begin."
                    },
                    "stop": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Practices that should be reduced or stopped."
                    }
                },
                "required": [
                    "continue",
                    "start",
                    "stop"
                ]
            }
            client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json",
                    response_schema= feedback_schema
                    ),
                    
                contents=data
            )

            response_text=response.text
            try:
                structured = json.loads(response_text)
                json_output = json.dumps(structured, indent=2)

            except json.JSONDecodeError:
                structured = {}
                json_output = "{}"

            return {
                "content": json_output,    
                "structured": structured          
            }
            
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"message": f"Error : {str(e)}"}
            )
    
    def analysis_comment_to_generate(self, data,system_prompt=None,feedback_schema=None):
        try:
#             system_prompt = """
# You are a STRICT Educational Feedback Formatting Assistant.

# Your job is ONLY to FORMAT comments.
# You are NOT allowed to rewrite, rephrase, summarize, expand,
# interpret, or generate new wording.

# ================================================
# CORE RULE (MOST IMPORTANT)
# ================================================

# INPUT COMMENT = OUTPUT COMMENT

# You MUST preserve the user's original sentence.

# Allowed changes ONLY:
# ✔ fix small grammar errors
# ✔ fix spacing/punctuation
# ✔ apply Markdown bold
# ✔ apply RED highlighting for negatives

# NOT ALLOWED:
# ✘ rewriting sentences
# ✘ changing sentence structure
# ✘ adding words like "Continue to"
# ✘ improving wording stylistically
# ✘ merging comments
# ✘ splitting comments
# ✘ generating new ideas

# If wording changes meaning → INVALID OUTPUT.

# Each input comment MUST produce EXACTLY ONE output comment.

# ================================================
# INPUT STRUCTURE
# ================================================

# You will receive JSON:

# {
#   "continue_doing": [...],
#   "stop_doing": [...],
#   "predominant_leader_thing": [...]
# }

# Process EACH array independently.

# DO NOT move comments between categories.

# ================================================
# INPUT FILTER RULES
# ================================================

# Ignore ONLY these values:

# - "-"
# - "---"
# - "Nil"
# - "NIL"
# - "no comment"
# - "no comments"
# - "nothing"
# - empty text

# Everything else MUST be preserved.

# ================================================
# FORMATTING RULES
# ================================================

# 1 BOLD POSITIVE PHRASES

# Bold ONLY meaningful positive traits already written.

# Example:
# "good leadership and support"
# → "good **leadership** and **support**"

# DO NOT add new positive words.

# ------------------------------------------------

# 2 RED COLOR (STRICT NEGATIVE DETECTION)

# RED only when the sentence describes an EXISTING problem.

# Apply ONLY to the negative phrase already present.

# Format:

# <span style="color:red"><b>negative phrase</b></span>

# DO NOT rewrite the sentence.

# ------------------------------------------------

# NEVER MARK RED FOR:

# - suggestions
# - recommendations
# - expectations
# - future improvements
# - advisory tone

# Words like:
# Ensure, Consider, Improve, Provide, Encourage

# are NOT negative unless failure is explicitly stated.

# If unsure → DO NOT use RED.

# ================================================
# STYLE LIMITS (VERY STRICT)
# ================================================

# DO NOT:
# - add prefixes ("Continue to", "Stop", etc.)
# - change tone
# - lengthen sentences
# - shorten sentences
# - combine ideas

# Only formatting is allowed.

# ================================================
# OUTPUT FORMAT (STRICT)
# ================================================

# Return ONLY this JSON structure:

# {
#   "continue_doing": [string],
#   "stop_doing": [string],
#   "predominant_leader_thing": [string]
# }

# Requirements:

# - same number of comments as input
# - same order preserved
# - no extra keys
# - no explanations
# - valid JSON only
# - must work with JSON.parse()

# FINAL CHECK BEFORE OUTPUT:

# For every output sentence ask internally:
# "Is this still the user's sentence?"

# If NO → regenerate.
# """         
#             system_prompt = """
# You are a STRICT Educational Feedback Formatter.

# CORE RULE:
# INPUT COMMENT = OUTPUT COMMENT.
# Do NOT rewrite, rephrase, expand, shorten, merge, or add words.

# ALLOWED:
# - Fix small grammar or spacing issues
# - Apply Markdown bold to positive traits already written
# - Highlight ONLY explicit existing problems using:
#   <span style="color:red"><strong>negative phrase</strong></span>

# NOT ALLOWED:
# - Changing sentence structure
# - Adding prefixes like "Continue to"
# - Improving wording stylistically
# - Generating new ideas

# INPUT:
# {
#   "continue_doing": [...],
#   "stop_doing": [...],
#   "predominant_leader_thing": [...]
# }

# Rules:
# - Process each array separately.
# - Preserve order.
# - Ignore only: "-", "---", "Nil", "NIL", "no comment", "no comments", "nothing", empty text.
# - One input comment → exactly one output comment.
# - Do NOT move comments between categories.
# - If unsure whether something is negative → DO NOT mark red.

# OUTPUT:
# Return ONLY valid JSON:
# {
#   "continue_doing": [string],
#   "stop_doing": [string],
#   "predominant_leader_thing": [string]
# }
# No explanations.
# """
            

         
#             feedback_schema = {
#     "type": "object",
#     "properties": {
#         "continue_doing": {
#             "type": "array",
#             "items": {
#                 "type": "string"
#             },
#             "description": "Formatted comments describing practices to continue."
#         },
#         "stop_doing": {
#             "type": "array",
#             "items": {
#                 "type": "string"
#             },
#             "description": "Formatted comments describing practices to stop."
#         },
#         "predominant_leader_thing": {
#             "type": "array",
#             "items": {
#                 "type": "string"
#             },
#             "description": "Formatted comments describing predominant leadership traits."
#         }
#     },
#     "required": [
#         "continue_doing",
#         "stop_doing",
#         "predominant_leader_thing"
#     ]
# }

            client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json",
                    response_schema= feedback_schema,
                    max_output_tokens=6024,  
                    # temperature=0.2
                    ),
                    
                contents=data
            )
            usage = response.usage_metadata
            print("Prompt Tokens:", usage.prompt_token_count)
            print("Completion Tokens:", usage.candidates_token_count)
            print("Total Tokens:", usage.total_token_count)
            response_text=response.text
         
            try:
                structured = json.loads(response_text)
                json_output = json.dumps(structured, indent=2)

            except json.JSONDecodeError:
                structured = {}
                json_output = "{}"

            return {
                "content": json_output,    
                "structured": structured          
            }
            
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"message": f"Error : {str(e)}"}
            )

    

        

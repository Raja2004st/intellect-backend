
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

       

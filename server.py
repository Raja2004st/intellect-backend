from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from Routes.feedbackRoutes import feedback_bp
import uvicorn
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"], 
)

app.include_router(feedback_bp)


@app.get("/health")
def health_check():
    try:
        db_status = "connected"
        status_code = 200
    except Exception as e:
        db_status = f"error: {str(e)}"
        status_code = 500

    return {"status": "healthy", "backend": db_status}, status_code

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))  
    print(f"Running on port: {port}")
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=True)
from fastapi import FastAPI
from pydantic import BaseModel
from engine import rank_jobs

api = FastAPI(title="SkillMatch API",
              description="Resume-to-internship matching engine")

class MatchRequest(BaseModel):
    resume_text: str
    top_k: int = 10

@api.get("/health")
def health():
    return {"status": "ok"}

@api.post("/match")
def match(body: MatchRequest):
    return {"results": rank_jobs(body.resume_text, body.top_k)}
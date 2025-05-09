from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from routers.schemas.models import Resume
from db.database import get_db
from db import models
from db.utils import get_gemini_client


router = APIRouter()

@router.post("/")
async def recommendations(resume: Resume, user_id: int, db: Session = Depends(get_db)):
    try:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        client = get_gemini_client()

        resume_text = f"""
        Name: {user.name}
        Resume Score: {resume.resume_score}
        No. Of Pages: {resume.no_of_pages}
        Skills: {', '.join(resume.skills)}
        Experience: {resume.total_experience}
        Level: {resume.user_level}
        """

        prompt = f"""
        You are an experienced HR Manager with Technical Experience in the field of any one job role from Data Science, Data Analyst, DevOPS, Machine Learning Engineer, Prompt Engineer, AI Engineer, Full Stack Web Development, Big Data Engineering, Marketing Analyst, Human Resource Manager, Software Developer. Your task is to review the provided resume.
        Please share your professional evaluation on whether the candidate's profile aligns with the role by highlighting their strengths and weaknesses. Also mention the Skills they already have and suggest some skills to improve their resume and suggest some courses they might take to improve the skills.

        Resume:
        {resume_text}
        """

        response = client.generate_content(
            prompt
        )

        resume = models.Resume(
            user_id=user_id,
            resume_score=resume.resume_score,
            no_of_pages=resume.no_of_pages,
            timestamp=resume.timestamp,
            recommendations=response.text,
            user_level=resume.user_level,
            skills=resume.skills,
            total_experience=resume.total_experience,
            job_description=resume.job_description,
        )
        db.add(resume)
        db.commit()

        return {"recommendations": response.text}

    except Exception as e:
        db.rollback()
        print(e)
        raise HTTPException(status_code=500, detail=str(e))
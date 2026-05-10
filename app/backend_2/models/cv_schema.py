from pydantic import BaseModel
from typing import List, Optional

class EducationEntry(BaseModel):
    institution: Optional[str] = None
    degree: Optional[str] = None

class ExperienceEntry(BaseModel):
    role: Optional[str] = None
    description: Optional[str] = None

class ProjectEntry(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class CVData(BaseModel):
    summary: Optional[str] = None
    education: List[EducationEntry] = []
    experience: List[ExperienceEntry] = []
    skills: List[str] = []
    projects: List[ProjectEntry] = []
    achievements: List[str] = []

class CVSignals(BaseModel):
    suggested_majors: List[str]
    confidence: float
    evidence: List[str]
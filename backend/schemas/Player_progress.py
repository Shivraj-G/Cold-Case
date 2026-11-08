from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal 

class Claim(BaseModel):
    who: str | None = None
    what: str
    where: str | None = None
    what: str | None = None

class Session(BaseModel):
    session_id : int
    case_id : int
    started_at : datetime
    questions_left : dict[str,int] #per suspect id

class Statement(BaseModel):
    session_id : str
    suspect_id : str
    turn : int
    text : str
    extracted_claims : list[Claim] = []

class Discovery(BaseModel):
    session_id : str
    evidence_id : str
    found_via : str #scene or suspect id

class Link(BaseModel):
    session_id : str
    entry_a : str
    entry_b : str
    type : Literal["contradicts","supports"]
    valid : bool

class SuspectState(BaseModel):
    session_id : str
    suspect_id : str
    stress : int = Field(ge=0,le=100)
    stance_history : list[str] = []
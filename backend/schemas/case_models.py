from pydantic import BaseModel
from typing import Literal
from enum import Enum

class Knowledge(str,Enum):
    KNOWS = "knows" 
    HIDES = "hides"
    LIES = "lies"

class Fact(BaseModel):
    id:str
    text:str
    time:str | None = None
    place:str | None = None
    people: list[str] = []

class FactKnowledge(BaseModel):
    fact_id: str
    status:Knowledge
    cover_story: str | None = None

class Character(BaseModel):
    id:str
    name:str
    persona: str
    traits: list[str] = [] #eg. proud,anxius 
    knowledge: list[FactKnowledge] = []
    role: Literal["suspect","victim","witness"] = "suspect"

class EvidenceItem(BaseModel):
    id:str
    name:str
    description:str
    proves:list[str] #fact ids
    scene: str #where is it

class Solution(BaseModel):
    culprit_id: str
    motive:str
    method:str
    evidence_chain: list[str] #evidence ids which leads to him

class CaseBible(BaseModel):
    id:str
    title:str
    facts : list[Fact]
    timeline : list[str] #fact ids in actual order
    characters : list[Character]
    evidence : list[EvidenceItem]
    solution : Solution
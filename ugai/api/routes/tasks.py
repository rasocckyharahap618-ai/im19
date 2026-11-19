from fastapi import APIRouter,HTTPException
from pydantic import BaseModel
from uuid import uuid4
router=APIRouter()
class TaskRequest(BaseModel): task:str; mode:str="FAST"
@router.post("/tasks",status_code=202)
def create_task(body:TaskRequest):
 if not body.task.strip(): raise HTTPException(422,"task must not be empty")
 return {"task_id":str(uuid4()),"status":"accepted","dispatch":"not_configured"}

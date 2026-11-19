from fastapi import APIRouter
router=APIRouter()
@router.get("/approvals")
def approvals(): return {"items":[],"status":"approval_backend_not_configured"}

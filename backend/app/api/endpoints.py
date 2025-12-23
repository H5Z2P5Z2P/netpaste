from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import FileResponse
from app.models.models import *
from app.services.redis_client import redis_client
from app.utils.security import generate_note_id, generate_token, generate_req_id, get_current_time, mask_ip
import os

router = APIRouter()

@router.post("/netcut/note/info/", response_model=NoteInfoResponse)
async def get_note_info(request: Request, req_data: NoteInfoRequest):
    """获取剪贴板内容"""
    req_id = generate_req_id()
    note_name = req_data.note_name
    
    # 获取客户端信息
    client_ip = request.client.host
    user_agent = request.headers.get("user-agent", "")
    client_type = "m" if "Mobile" in user_agent else "pc"
    
    # 从Redis获取数据 (Async)
    note_data = await redis_client.get_note(note_name)
    
    if not note_data:
        # 创建新的剪贴板
        current_time = get_current_time()
        note_id = generate_note_id()
        note_token = generate_token()
        
        log_entry = {
            "client": client_type,
            "ip": mask_ip(client_ip),
            "location": "本地",
            "time": current_time
        }
        
        note_data = {
            "note_id": note_id,
            "note_name": note_name,
            "note_content": "",
            "note_token": note_token,
            "created_time": current_time,
            "updated_time": current_time,
            "last_read_time": current_time,
            "read_count": 1,
            "expire_time": 2592000,
            "file_list": [],
            "log_list": [log_entry],
            "note_pwd": "",
            "has_password": False
        }
        
        # Async Save
        await redis_client.save_note(note_name, note_data, note_data.get("expire_time"))
    else:
        # 验证密码（如果设置了密码）
        stored_password = note_data.get("note_pwd", "")
        if stored_password and stored_password != req_data.note_pwd:
            return NoteInfoResponse(
                status=0,
                data=None,
                req_id=req_id,
                error="密码错误"
            )
        
        # 更新访问记录
        current_time = get_current_time()
        note_data["last_read_time"] = current_time
        note_data["read_count"] += 1
        
        log_entry = {
            "client": client_type,
            "ip": mask_ip(client_ip),
            "location": "本地", 
            "time": current_time
        }
        
        # 保持最近20条日志
        note_data["log_list"].insert(0, log_entry)
        if len(note_data["log_list"]) > 20:
            note_data["log_list"] = note_data["log_list"][:20]
            
        # Async Save
        await redis_client.save_note(note_name, note_data, note_data.get("expire_time"))
    
    # 设置has_password字段但不返回实际密码
    note_data["has_password"] = bool(note_data.get("note_pwd", ""))
    if note_data.get("note_pwd"):
        note_data["note_pwd"] = ""  # 不返回实际密码给前端
    
    return NoteInfoResponse(
        status=1,
        data=NoteData(**note_data),
        req_id=req_id
    )

@router.post("/netcut/note/save/", response_model=NoteSaveResponse)
async def save_note(req_data: NoteSaveRequest):
    """保存剪贴板内容"""
    req_id = generate_req_id()
    note_name = req_data.note_name
    
    # 获取当前数据 (Async)
    note_data = await redis_client.get_note(note_name)
    
    if not note_data:
        return NoteSaveResponse(
            status=0,
            error="剪贴板不存在",
            req_id=req_id
        )
    
    # Prepare new data
    current_time = get_current_time()
    new_token = generate_token()
    
    # Create a copy to update
    new_note_data = note_data.copy()
    new_note_data["note_content"] = req_data.note_content
    new_note_data["note_token"] = new_token
    new_note_data["updated_time"] = current_time
    
    # 处理密码设置
    if req_data.note_pwd:
        new_note_data["note_pwd"] = req_data.note_pwd
        new_note_data["has_password"] = True
    
    # 处理过期时间
    expire_time = req_data.expire_time if req_data.expire_time > 0 else None
    new_note_data["expire_time"] = req_data.expire_time
    
    # 使用原子操作更新 (Atomic Update)
    success, error_msg = await redis_client.update_note_atomic(
        note_name=note_name,
        old_token=req_data.note_token,
        new_data=new_note_data,
        expire_time=expire_time
    )
    
    if success:
        return NoteSaveResponse(
            status=1,
            data={
                "note_id": new_note_data["note_id"],
                "note_token": new_token,
                "time": current_time
            },
            req_id=req_id
        )
    else:
        # If it's a token error, we might want to convey that specifically?
        # For now, sticking to the existing response structure but with clearer error
        return NoteSaveResponse(
            status=0,
            error=error_msg or "保存失败",
            req_id=req_id
        )

@router.get("/{note_name}")
@router.get("/{note_name}/")
async def get_note_page(note_name: str):
    """返回剪贴板详情页面"""
    # Exclude reserved paths or files that might match single path segment
    if note_name in ["assets", "favicon.ico", "robots.txt"]:
        return FileResponse(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "frontend", note_name))
        
    note_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "frontend", "note.html")
    return FileResponse(note_file_path)
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.api import deps
from app.crud import message as message_crud
from app.models.message import Message
from app.schemas.message import MessageCreate, MessageOut

router = APIRouter(prefix="/message", tags=["message"])


@router.get("/list", response_model=list[MessageOut])
def list_messages(current=Depends(deps.get_current_user), db: Session = Depends(deps.get_db)):
    """获取当前用户的消息列表"""
    try:
        return message_crud.message.list_for_user(db, current.user_id)
    except Exception as e:
        from app.core.logging import logger
        import traceback
        logger.error(f"获取消息列表失败: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"获取消息列表失败: {str(e)}")


@router.get("/unread-count")
def get_unread_count(current=Depends(deps.get_current_user), db: Session = Depends(deps.get_db)):
    """获取未读消息数量"""
    try:
        count = db.query(Message).filter(
            Message.to_user_id == current.user_id,
            Message.is_read == 0
        ).count()
        return {"unread_count": count}
    except Exception as e:
        from app.core.logging import logger
        logger.error(f"获取未读消息数量失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取未读消息数量失败: {str(e)}")


@router.put("/{message_id}/read")
def mark_message_as_read(
    message_id: int,
    current=Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """标记单条消息为已读"""
    try:
        message = db.query(Message).filter(Message.message_id == message_id).first()
        
        if not message:
            raise HTTPException(status_code=404, detail="消息不存在")
        
        # 验证权限
        if message.to_user_id != current.user_id:
            raise HTTPException(status_code=403, detail="无权操作此消息")
        
        # 标记为已读
        if message.is_read == 0:
            message.is_read = 1
            message.read_time = datetime.now()
            db.commit()
        
        return {"success": True, "message": "已标记为已读"}
    except HTTPException:
        raise
    except Exception as e:
        from app.core.logging import logger
        logger.error(f"标记消息已读失败: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"标记消息已读失败: {str(e)}")


@router.put("/read-all")
def mark_all_as_read(current=Depends(deps.get_current_user), db: Session = Depends(deps.get_db)):
    """标记所有消息为已读"""
    try:
        count = message_crud.message.mark_all_as_read(db, current.user_id)
        
        # 同时更新 read_time
        db.query(Message).filter(
            Message.to_user_id == current.user_id,
            Message.is_read == 1,
            Message.read_time.is_(None)
        ).update({"read_time": datetime.now()})
        db.commit()
        
        return {
            "success": True,
            "message": f"已标记{count}条消息为已读",
            "count": count
        }
    except Exception as e:
        from app.core.logging import logger
        logger.error(f"批量标记已读失败: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"批量标记已读失败: {str(e)}")


@router.delete("/{message_id}")
def delete_message(
    message_id: int,
    current=Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """删除单条消息
    
    物理删除消息记录
    """
    try:
        message = db.query(Message).filter(Message.message_id == message_id).first()
        
        if not message:
            raise HTTPException(status_code=404, detail="消息不存在")
        
        # 验证权限（只能删除发给自己的消息）
        if message.to_user_id != current.user_id:
            raise HTTPException(status_code=403, detail="无权删除此消息")
        
        # 物理删除
        db.delete(message)
        db.commit()
        
        from app.core.logging import logger
        logger.info(f"用户 {current.user_id} 删除了消息 {message_id}")
        
        return {"success": True, "message": "消息已删除", "message_id": message_id}
    except HTTPException:
        raise
    except Exception as e:
        from app.core.logging import logger
        logger.error(f"删除消息失败 message_id={message_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除消息失败: {str(e)}")


@router.delete("/batch/delete")
def batch_delete_messages(
    message_ids: list[int],
    current=Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """批量删除消息
    
    Args:
        message_ids: 消息ID列表
    
    Returns:
        删除结果
    """
    try:
        if not message_ids:
            raise HTTPException(status_code=400, detail="消息ID列表不能为空")
        
        # 查询要删除的消息
        messages = db.query(Message).filter(
            Message.message_id.in_(message_ids),
            Message.to_user_id == current.user_id  # 只能删除发给自己的消息
        ).all()
        
        deleted_count = len(messages)
        
        # 批量删除
        for message in messages:
            db.delete(message)
        
        db.commit()
        
        from app.core.logging import logger
        logger.info(f"用户 {current.user_id} 批量删除了 {deleted_count} 条消息")
        
        return {
            "success": True,
            "message": f"已删除 {deleted_count} 条消息",
            "deleted_count": deleted_count
        }
    except HTTPException:
        raise
    except Exception as e:
        from app.core.logging import logger
        logger.error(f"批量删除消息失败: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"批量删除消息失败: {str(e)}")


@router.delete("/clear")
def clear_all_messages(
    current=Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """清空所有消息
    
    删除当前用户的所有消息
    """
    try:
        deleted_count = db.query(Message).filter(
            Message.to_user_id == current.user_id
        ).delete()
        
        db.commit()
        
        from app.core.logging import logger
        logger.info(f"用户 {current.user_id} 清空了所有消息，共 {deleted_count} 条")
        
        return {
            "success": True,
            "message": f"已清空所有消息",
            "deleted_count": deleted_count
        }
    except Exception as e:
        from app.core.logging import logger
        logger.error(f"清空消息失败: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"清空消息失败: {str(e)}")


@router.post("/send", response_model=MessageOut)
def send_message(
    payload: MessageCreate,
    current=Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
):
    """发送消息"""
    from app.utils.pydantic import get_model_data
    message_data = get_model_data(payload)
    message_data["from_user_id"] = current.user_id
    db_obj = message_crud.message.create_by_dict(db, message_data)
    return db_obj



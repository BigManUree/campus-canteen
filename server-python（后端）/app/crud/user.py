from typing import Optional

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.crud.base import CRUDBase
from app.models.user import User
from app.schemas.user import UserCreate
from app.utils.pydantic import get_model_data


class CRUDUser(CRUDBase[User, UserCreate]):
    def get_by_username(self, db: Session, username: str) -> Optional[User]:
        """按用户名查询用户，用于登录和注册时的唯一性校验。"""
        return db.query(User).filter(User.username == username).first()

    def get_by_phone(self, db: Session, phone: str) -> Optional[User]:
        """按手机号查询用户，用于手机号登录或绑定校验。"""
        return db.query(User).filter(User.phone == phone).first()

    def get_by_username_or_phone(self, db: Session, identifier: str) -> Optional[User]:
        """根据用户名或手机号查找用户，支持统一登录入口。"""
        return db.query(User).filter(
            (User.username == identifier) | (User.phone == identifier)
        ).first()

    def create(self, db: Session, obj_in: UserCreate) -> User:
        """创建用户前对密码加密，并将角色枚举统一转换为数据库可保存的字符串。"""
        # 使用工具函数处理 Pydantic 数据
        try:
            data = get_model_data(obj_in, exclude={"password"}, mode="python")
        except TypeError:
            # 如果 mode 参数不支持，使用默认方式
            data = get_model_data(obj_in, exclude={"password"})
        
        data["password"] = hash_password(obj_in.password)
        
        # 处理role枚举值，转换为字符串（Pydantic枚举在model_dump后可能还是枚举对象）
        if "role" in data:
            role_value = data["role"]
            # 如果是枚举对象，获取其值
            if hasattr(role_value, "value"):
                data["role"] = role_value.value
            elif isinstance(role_value, str):
                pass  # 已经是字符串
            else:
                # 尝试转换为字符串
                data["role"] = str(role_value) if role_value else "user"
        
        # 确保role是字符串类型
        if "role" not in data or not isinstance(data.get("role"), str):
            data["role"] = "user"
        
        db_obj = User(**data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update_status(self, db: Session, id: int, status: int) -> Optional[User]:
        """更新用户状态"""
        return self.update_by_dict(db, id, {"status": status})
    
    def update_role(self, db: Session, id: int, role: str) -> Optional[User]:
        """更新用户角色"""
        # 处理枚举值
        if hasattr(role, "value"):
            role = role.value
        elif not isinstance(role, str):
            role = str(role)
        return self.update_by_dict(db, id, {"role": role})
    
    def update_password(self, db: Session, id: int, new_password: str) -> Optional[User]:
        """更新用户密码"""
        hashed_password = hash_password(new_password)
        return self.update_by_dict(db, id, {"password": hashed_password})
    
    def delete(self, db: Session, id: int) -> bool:
        """删除用户(级联删除相关数据)"""
        from sqlalchemy.exc import IntegrityError
        from app.core.logging import logger
        
        user = db.query(User).filter(User.user_id == id).first()
        if not user:
            return False
        
        try:
            # 删除用户相关的所有数据
            self._delete_user_related_data(db, id)
            
            # 删除用户
            db.delete(user)
            db.commit()
            return True
        except IntegrityError as e:
            db.rollback()
            logger.error(f"删除用户 {id} 失败: {str(e)}")
            raise ValueError(f"无法删除用户: 存在关联数据")
        except Exception as e:
            db.rollback()
            logger.error(f"删除用户 {id} 时发生异常: {str(e)}")
            raise ValueError(f"删除用户失败: {str(e)}")
    
    def batch_delete(self, db: Session, ids: list[int]) -> int:
        """批量删除用户(级联删除相关数据)"""
        from sqlalchemy.exc import IntegrityError
        from app.core.logging import logger
        
        try:
            # 批量删除用户相关的所有数据
            for user_id in ids:
                self._delete_user_related_data(db, user_id)
            
            # 批量删除用户
            count = db.query(User).filter(User.user_id.in_(ids)).delete(synchronize_session=False)
            db.commit()
            return count
        except IntegrityError as e:
            db.rollback()
            logger.error(f"批量删除用户失败: {str(e)}")
            raise ValueError(f"无法批量删除用户: 存在关联数据")
        except Exception as e:
            db.rollback()
            logger.error(f"批量删除用户时发生异常: {str(e)}")
            raise ValueError(f"批量删除用户失败: {str(e)}")
    
    def _delete_user_related_data(self, db: Session, user_id: int):
        """删除用户相关的所有数据"""
        from sqlalchemy import text
        from app.core.logging import logger
        
        # 按照外键依赖顺序删除相关数据
        # 必须先删除引用 orders 的子表,再删除 orders,最后删除其他用户相关表
        
        # 第一步: 删除引用 orders 表的子表数据
        # 这些表通过 order_id 引用 orders 表,而 orders 表又引用 users 表
        order_child_tables = [
            ("canteen_reviews", "order_id"),   # 食堂评论
            ("refunds", "order_id"),           # 退款
            ("reviews", "order_id"),           # 菜品评论
            ("order_items", "order_id"),       # 订单项
            # ("queue_records", "order_id"),   # 排队记录(表不存在,已注释)
        ]
        
        for table, fk_column in order_child_tables:
            try:
                sql = f"""
                DELETE FROM {table} 
                WHERE {fk_column} IN (
                    SELECT order_id FROM orders WHERE user_id = :user_id
                )
                """
                result = db.execute(text(sql), {"user_id": user_id})
                if result.rowcount > 0:
                    logger.info(f"删除用户 {user_id} 的 {table} 表数据: {result.rowcount} 条")
            except Exception as e:
                logger.warning(f"清理 {table} 表失败: {str(e)}")
        
        # 第二步: 删除 user_coupons 中引用 orders 的记录
        try:
            sql = """
            DELETE FROM user_coupons 
            WHERE used_order_id IN (
                SELECT order_id FROM orders WHERE user_id = :user_id
            )
            """
            result = db.execute(text(sql), {"user_id": user_id})
            if result.rowcount > 0:
                logger.info(f"删除用户 {user_id} 的 user_coupons(订单关联) 表数据: {result.rowcount} 条")
        except Exception as e:
            logger.warning(f"清理 user_coupons(订单关联) 表失败: {str(e)}")
        
        # 第三步: 删除 messages 中引用 orders 的记录
        try:
            sql = """
            DELETE FROM messages 
            WHERE order_id IN (
                SELECT order_id FROM orders WHERE user_id = :user_id
            )
            """
            result = db.execute(text(sql), {"user_id": user_id})
            if result.rowcount > 0:
                logger.info(f"删除用户 {user_id} 的 messages(订单关联) 表数据: {result.rowcount} 条")
        except Exception as e:
            logger.warning(f"清理 messages(订单关联) 表失败: {str(e)}")
        
        # 第四步: 删除用户直接关联的表(包括 orders)
        user_direct_tables = [
            "browse_history",      # 浏览历史
            "favorites",           # 收藏
            "cart_items",          # 购物车
            "orders",              # 订单(子表已删除)
            "user_addresses",      # 地址
            "user_coupons",        # 用户优惠券(剩余的)
        ]
        
        for table in user_direct_tables:
            try:
                result = db.execute(
                    text(f"DELETE FROM {table} WHERE user_id = :user_id"), 
                    {"user_id": user_id}
                )
                if result.rowcount > 0:
                    logger.info(f"删除用户 {user_id} 的 {table} 表数据: {result.rowcount} 条")
            except Exception as e:
                logger.warning(f"清理 {table} 表失败: {str(e)}")
        
        # 第五步: 清理档口对商家用户的绑定
        try:
            result = db.execute(
                text("UPDATE canteens SET merchant_user_id = NULL WHERE merchant_user_id = :user_id"),
                {"user_id": user_id}
            )
            if result.rowcount > 0:
                logger.info(f"清理用户 {user_id} 的档口绑定: {result.rowcount} 条")
        except Exception as e:
            logger.warning(f"清理档口绑定失败: {str(e)}")
        
        # 第六步: 删除 notifications 表中的用户通知
        try:
            result = db.execute(
                text("DELETE FROM notifications WHERE user_id = :user_id"),
                {"user_id": user_id}
            )
            if result.rowcount > 0:
                logger.info(f"删除用户 {user_id} 的 notifications 表数据: {result.rowcount} 条")
        except Exception as e:
            logger.warning(f"清理 notifications 表失败: {str(e)}")
        
        # 第七步: 删除 messages 中用户作为发送者或接收者的记录
        try:
            result = db.execute(
                text("DELETE FROM messages WHERE from_user_id = :user_id OR to_user_id = :user_id"), 
                {"user_id": user_id}
            )
            if result.rowcount > 0:
                logger.info(f"删除用户 {user_id} 的 messages(用户关联) 表数据: {result.rowcount} 条")
        except Exception as e:
            logger.warning(f"清理 messages(用户关联) 表失败: {str(e)}")
        
        # 提交删除操作
        db.flush()
    
    def batch_update_status(self, db: Session, ids: list[int], status: int) -> int:
        """批量更新用户状态"""
        count = db.query(User).filter(User.user_id.in_(ids)).update(
            {"status": status}, synchronize_session=False
        )
        db.commit()
        return count
    
    def batch_update_role(self, db: Session, ids: list[int], role: str) -> int:
        """批量更新用户角色"""
        # 处理枚举值
        if hasattr(role, "value"):
            role = role.value
        elif not isinstance(role, str):
            role = str(role)
        
        count = db.query(User).filter(User.user_id.in_(ids)).update(
            {"role": role}, synchronize_session=False
        )
        db.commit()
        return count


user = CRUDUser(User)


from datetime import datetime
from typing import List
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import and_, select

from app.crud.base import CRUDBase
from app.models.coupon import Coupon, UserCoupon
from app.schemas.coupon import CouponCreate, CouponUpdate


class CRUDCoupon(CRUDBase[Coupon, CouponCreate]):
    def calculate_discount(self, coupon: Coupon, order_amount: Decimal) -> Decimal:
        """计算优惠金额。折扣券约定 discount_value=8 表示 8 折，即优惠 20%。"""
        if coupon.coupon_type == "discount":
            discount_rate = Decimal(str(coupon.discount_value))
            if discount_rate <= 0:
                return Decimal("0")

            if discount_rate <= 1:
                discount = order_amount * (Decimal("1") - discount_rate)
            elif discount_rate <= 10:
                discount = order_amount * (Decimal("1") - discount_rate / Decimal("10"))
            else:
                discount = order_amount * (Decimal("1") - discount_rate / Decimal("100"))

            discount = max(Decimal("0"), discount)
            if coupon.max_discount:
                discount = min(discount, Decimal(str(coupon.max_discount)))
            return discount

        return Decimal(str(coupon.discount_value or 0))

    def list_available(self, db: Session, user_id: int = None) -> List[Coupon]:
        """获取可用优惠券列表（包括即将开始的优惠券）"""
        now = datetime.now()
        query = db.query(Coupon).filter(
            and_(
                Coupon.status == 1,
                Coupon.end_time >= now  # 只要优惠券未结束就显示
            )
        ).order_by(Coupon.start_time.asc())  # 按开始时间排序

        # 如果指定了用户，排除已领取的
        if user_id:
            used_coupon_ids = db.query(UserCoupon.coupon_id).filter(
                UserCoupon.user_id == user_id
            ).subquery()
            query = query.filter(~Coupon.coupon_id.in_(select(used_coupon_ids.c.coupon_id)))

        return query.all()

    def get_user_coupons(self, db: Session, user_id: int, status: int = None) -> List[UserCoupon]:
        """获取用户优惠券"""
        query = db.query(UserCoupon).filter(UserCoupon.user_id == user_id)
        if status is not None:
            query = query.filter(UserCoupon.status == status)
        return query.order_by(UserCoupon.get_time.desc()).all()

    def claim_coupon(self, db: Session, user_id: int, coupon_id: int) -> UserCoupon:
        """领取优惠券"""
        coupon = self.get(db, coupon_id)
        if not coupon:
            raise ValueError("优惠券不存在")

        now = datetime.now()
        if coupon.status != 1:
            raise ValueError("优惠券已禁用")
        if coupon.start_time > now or coupon.end_time < now:
            raise ValueError("优惠券不在有效期内")
        if coupon.total_count > 0 and coupon.used_count >= coupon.total_count:
            raise ValueError("优惠券已领完")

        # 检查是否已领取（包括已使用的）
        existing = db.query(UserCoupon).filter(
            and_(
                UserCoupon.user_id == user_id,
                UserCoupon.coupon_id == coupon_id
            )
        ).first()
        if existing:
            if existing.status == 0:
                raise ValueError("您已领取过此优惠券且未使用")
            else:
                raise ValueError("您已领取并使用过此优惠券，无法重复领取")

        # 创建用户优惠券
        user_coupon = UserCoupon(
            user_id=user_id,
            coupon_id=coupon_id,
            expire_time=coupon.end_time
        )
        db.add(user_coupon)

        # 更新优惠券领取数量
        coupon.used_count += 1
        db.commit()
        db.refresh(user_coupon)
        return user_coupon

    def use_coupon(self, db: Session, user_id: int, coupon_id: int, order_id: int, order_amount: Decimal) -> Decimal:
        """使用优惠券，返回优惠金额"""
        user_coupon = db.query(UserCoupon).filter(
            and_(
                UserCoupon.user_id == user_id,
                UserCoupon.coupon_id == coupon_id,
                UserCoupon.status == 0
            )
        ).first()

        if not user_coupon:
            raise ValueError("优惠券不存在或已使用")

        coupon = user_coupon.coupon
        now = datetime.now()
        if now > user_coupon.expire_time:
            raise ValueError("优惠券已过期")

        if order_amount < coupon.min_amount:
            raise ValueError(f"订单金额需满{coupon.min_amount}元")

        # 计算优惠金额
        discount = self.calculate_discount(coupon, order_amount)

        # 更新用户优惠券状态
        user_coupon.status = 1
        user_coupon.used_time = now
        user_coupon.used_order_id = order_id

        db.commit()
        return discount


coupon = CRUDCoupon(Coupon)

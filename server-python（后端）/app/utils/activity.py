"""
Activity 工具函数
用于处理活动模型输出
"""

from app.models.activity import Activity
from app.schemas.activity import ActivityOut


def parse_activity_json(activity: Activity) -> ActivityOut:
    """将活动 ORM 对象转换为对外输出结构，并补全图片访问地址。"""
    from app.utils.image import convert_to_full_url

    return ActivityOut(
        activity_id=activity.activity_id,
        title=activity.title,
        subtitle=activity.subtitle,
        content=activity.content,
        cover_image=convert_to_full_url(activity.cover_image),
        organizer=activity.organizer,
        location=activity.location,
        contact_name=activity.contact_name,
        contact_phone=activity.contact_phone,
        start_time=activity.start_time,
        end_time=activity.end_time,
        status=activity.status if activity.status is not None else 1,
        sort_order=activity.sort_order if activity.sort_order is not None else 0,
        create_time=activity.create_time,
        update_time=activity.update_time,
    )


def prepare_activity_update_data(update_data: dict) -> dict:
    """预处理活动更新数据，保留扩展清洗或字段转换的入口。"""
    return update_data

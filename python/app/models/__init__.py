"""模型聚合导入,确保 ``Base.metadata`` 收集到所有实体。"""
from app.models.user import User

__all__ = ["User"]

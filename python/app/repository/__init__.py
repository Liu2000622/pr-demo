"""仓储层聚合。"""
from app.repository import user_repository as user_repo

# 暴露为 ``repository.find_by_username`` 等,便于调用。
find_by_username = user_repo.find_by_username
find_all_by_username = user_repo.find_all_by_username
count_by_username = user_repo.count_by_username
find_all_users = user_repo.find_all
save_user = user_repo.save
delete_user = user_repo.delete

__all__ = [
    "user_repo",
    "find_by_username",
    "find_all_by_username",
    "count_by_username",
    "find_all_users",
    "save_user",
    "delete_user",
]

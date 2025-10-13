from .db_add import add_user, add_elective, add_feedback
from .delete_Info import delete_user, delete_feedback, delete_course

__all__ = [
    "add_user", "add_elective", "add_feedback",
    "delete_user", "delete_feedback", "delete_course"
]
"""互換用の入口。問題データの管理元は data/questions.xlsx です。"""
from quiz_database import LEVEL_INFOS, generate_question, reload_database

reload_database()

import requests
import re
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from django.conf import settings
# --------------------------functions below used for phones----------------------------------------------------
from django.forms.models import model_to_dict
from django.db.models.fields.files import FieldFile

# safe_model_to_dict()：用于 返回 友好的 JSON
def safe_model_to_dict(instance, exclude=[]):
    data = model_to_dict(instance)

    for key, value in data.items():
        if isinstance(value, FieldFile):  # ImageField / FileField
            try:
                data[key] = value.url
            except ValueError:
                data[key] = None

        elif isinstance(value, list):
            # 尝试把 Enum / choices 类型的 list 转为 string list
            data[key] = [str(item.name if hasattr(item, 'name') else item) for item in value]

        elif hasattr(value, 'isoformat'):
            data[key] = value.isoformat()

        elif isinstance(value, bytes):
            data[key] = value.decode('utf-8', errors='ignore')

        elif hasattr(value, 'name') and isinstance(value.__class__, type):
            data[key] = value.name  # 处理单个 Enum 类型

        elif not isinstance(value, (str, int, float, bool, type(None), dict)):
            data[key] = str(value)

    for field in exclude:
        if field in data:
            del data[field]

    return data

# parse_enum_list()：用于 接收 前端传来的字符串并转换为后端可识别的枚举值
def parse_enum_list(enum_class, string_list):
    """
    将字符串列表（如 ['PTSD', 'Depression']）转换为指定 Enum 类的对象列表。

    参数:
        enum_class: 枚举类，例如 ConditionType、SupportType 等。
        string_list: 前端传来的字符串列表。

    返回:
        枚举对象列表。例如 [ConditionType.PTSD, ConditionType.DEPRESSION]
    """
    if not isinstance(string_list, list):
        return []  # 安全防御

    return [
        enum_class[item]
        for item in string_list
        if isinstance(item, str) and item in enum_class.__members__
    ]

# 实时更新数据库数据

# encoding: utf-8
import base64
from datetime import datetime
import hashlib
import hmac
import random
import string
import time
import uuid

from config import TILAKE_UTILS_X_TILAKE_APP_KEY, TILAKE_UTILS_X_TILAKE_APP_SECRET, TILAKE_UTILS_X_TILAKE_CA_SIGNATURE_METHOD


def generate_signature(method, accept, content_type, date, url_path, app_secret=TILAKE_UTILS_X_TILAKE_APP_SECRET):
    """
    生成签名
    :param method:
    :param accept:
    :param content_type:
    :param date:
    :param url_path:
    :return:
    """
    string_to_sign = method + "\n" + accept + "\n" + content_type + "\n" + date + "\n" + url_path
    string_to_sign = string_to_sign.encode('utf-8')
    secret_key = app_secret.encode('utf-8')
    signature = hmac.new(secret_key, string_to_sign, hashlib.sha256).digest()
    return encode_base64_string(signature)


def generate_random_string(length=16):
    """
    生成随机串
    :param length: 随机串长度，默认为 16
    :return: 随机串
    """
    letters = string.ascii_letters + string.digits
    rand_str = ''.join(random.choice(letters) for i in range(length))
    return rand_str


def get_current_time(format='%Y-%m-%d %H:%M:%S'):
    """
    获取当前时间
    :param format: 时间格式，默认为 '%H:%M:%S'
    :return: 当前时间字符串
    """
    now = datetime.now()
    time_str = now.strftime(format)
    return time_str


def get_current_timestamp():
    """
    获取当前时间时间戳
    :return:
    """
    timestamp_str = int(round(time.time() * 1000))
    return str(timestamp_str)


def encode_base64_string(s):
    """
    对字符串进行 Base64 编码
    :param s: 字符串
    :return: 编码后的字符串
    """
    encoded = base64.b64encode(s).decode()
    return encoded


def generate_uuid_str():
    """
    获取uuid
    :return:
    """
    uid = str(uuid.uuid4())
    uuid_str = ''.join(uid.split('-'))
    return uuid_str


def get_current_time_gmt_format():
    """
    获取当前时间的GMT 时间
    :return:
    """
    GMT_FORMAT = '%a, %d %b %Y %H:%M:%SGMT+00:00'
    now = datetime.now()
    time_str = now.strftime(GMT_FORMAT)
    return time_str


def generate_header(content_type, accept, date, signature, app_key=TILAKE_UTILS_X_TILAKE_APP_KEY, ca_signature_method=TILAKE_UTILS_X_TILAKE_CA_SIGNATURE_METHOD):
    """
    生成请求头参数
    :param content_type:
    :param accept:
    :return:
    """
    headers = {'x-tilake-app-key': app_key,
               'x-tilake-ca-signature-method': ca_signature_method,
               'x-tilake-ca-timestamp': get_current_timestamp(),
               'x-tilake-ca-nonce': generate_random_string(),
               'x-tilake-ca-signature': signature,
               'Date': date,
               'Content-Type': content_type,
               'Accept': accept}
    return headers
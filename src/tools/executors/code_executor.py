# encoding: utf-8
import requests
import traceback
import time
import json

from utils.tilake_utils import generate_header, generate_signature, get_current_time_gmt_format
from .base_executor import BaseExecutor
from config import CODE_RUNNER_API_URL, CODE_RUNNER_API_SUB_URL
from utils.common_utils import print_logs

class CodeExecutor(BaseExecutor):

    def execute(self, code, *args, **kwargs):
        user_id = kwargs.get("user_id", "")
        conversation_id = kwargs.get("conversation_id", "")
        dialogue_id = kwargs.get("dialogue_id", "")
        request_id = kwargs.get("request_id", "")
        question = kwargs.get("question", "")

        
        
        code_prefix = """import matplotlib
import matplotlib.pyplot as plt

matplotlib.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams["axes.unicode_minus"] = False #该语句解决图像中的“-”负号的乱码
"""
        date = get_current_time_gmt_format()
        content_type = 'application/json'
        accept = '*/*'
        method = 'POST'
        url_path = CODE_RUNNER_API_SUB_URL
        signature_str = generate_signature(method=method, accept=accept, content_type=content_type, date=date,
                                            url_path=url_path)

        url = CODE_RUNNER_API_URL
        data = {
            'id': "1111",
            'code_text': code_prefix + "\n" + code,
        }

        headers = generate_header(content_type=content_type, accept=accept, date=date, signature=signature_str)

        start_time = time.time()
        input_params = data
        output_params = {}
        remote_res = {"remote_name": "code runner sandbox", "remote_url": CODE_RUNNER_API_URL, "remote_input_parameter": json.dumps({"headers": headers, "data": data}, ensure_ascii=False)}
        print_logs(question=question, input_parameter=input_params, user_id=user_id, conversation_id=conversation_id, dialogue_id=dialogue_id, request_id=request_id, start_time=time.time(), stage_name="code runner start", remote_mes=remote_res, traceback_info=traceback.extract_stack())

        response = requests.post(url, json=data, headers=headers).json()

        output_params = response
        remote_res["remote_output_parameter"] = json.dumps(response, ensure_ascii=False)
        print_logs(question=question, input_parameter=input_params, output_parameter=output_params, user_id=user_id, conversation_id=conversation_id, dialogue_id=dialogue_id, request_id=request_id, start_time=time.time(), stage_name="code runner end", remote_mes=remote_res, traceback_info=traceback.extract_stack(), service_cost_total=round(time.time()-start_time, 3))
        return response['data']
'''
Author: 陈瑶 1271650511@qq.com
Date: 2025-03-25 16:24:57
LastEditors: 陈瑶 1271650511@qq.com
LastEditTime: 2025-03-26 11:21:52
FilePath: /DeepLiterature/src/agents/planner_agent.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''
# encoding: utf-8
import time
import json
import re
import json_repair

from llms.base_llm import BaseLLM
from utils.logger import model_logger
from .base_agent import BaseAgent
from .prompts.planner_agent_prompts import SYSTEM_PROMPT_EN, SYSTEM_PROMPT_ZH
from retrying import retry

class PlannerAgent(BaseAgent):
    def __init__(self, llm: BaseLLM, lang: str):
        self.llm = llm
        self.lang = lang
    
    def postprocess(self, response):
        
        @retry(stop_max_attempt_number=3, wait_fixed=1000)
        def parse_response(response):
            return json_repair.loads(response)

        try:
            parsed_plan = parse_response(response)
        except json.JSONDecodeError as e:
            raise e
        return parsed_plan

    def run(self, query, snippet_list=None, temperature=0.3, max_tokens=2048):
        start_time = time.time()
        user_prompt = ""
        systemt_prompt = ""
        if self.lang == "zh":
            user_prompt = f"问题: + {query}"
            systemt_prompt = SYSTEM_PROMPT_ZH
        elif self.lang == "en":
            user_prompt = f"Question: + {query}"
            systemt_prompt = SYSTEM_PROMPT_EN

        response = ""
        reasoning_content = ""
        for label, cont in self.llm.stream_chat(system_content=systemt_prompt, user_content=user_prompt, temperature=temperature, max_tokens=max_tokens, answer_sleep=0):
            if label == "think":
                reasoning_content = cont
                yield label, reasoning_content
            else:
                response += cont
        res = self.postprocess(response)
        in_out = {"state": "parse_classify", "input": {"question": query, "snippet_list": snippet_list, "temperature": temperature, "max_tokens": max_tokens}, \
                "output": res, "response": {"content":response, "reasoning_content": reasoning_content}, "user_prompt": user_prompt, "cost_time": str(round(time.time()-start_time, 3))}
        model_logger.info(json.dumps(in_out, ensure_ascii=False))
        yield "answer", res
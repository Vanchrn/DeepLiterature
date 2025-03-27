'''
Author: 陈瑶 1271650511@qq.com
Date: 2025-03-21 10:58:39
LastEditors: 陈瑶 1271650511@qq.com
LastEditTime: 2025-03-27 21:05:02
FilePath: /DeepLiterature/src/service/api.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''
# encoding: utf-8
from fastapi import FastAPI, Request
import uvicorn, json
from fastapi.responses import StreamingResponse
import logging
from queue import Queue
import threading
import sys,os
import pickle
# os.environ["http_proxy"]="http://127.0.0.1"
# os.environ["https_proxy"]="https://127.0.0.1"
# os.environ["no_proxy"]=""
ROOT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT_PATH)
from utils.message_queue import WrapperQueue
from workflow import deepresearch_workflow
from config import LANGUAGE
from tqdm import tqdm

def generator(wrapper_queue):
    while True:
        message = wrapper_queue.get()
        if message == "finish":
            yield "data: [DONE]\n\n"
            return
        if message == "exception":
            yield "data: [ERROR]\n\n"
            return
        if type(message) == type(dict()):
            message = json.dumps(message, ensure_ascii=False)
        yield f"data: {message}\n\n"


app = FastAPI()

@app.post("/stream")
async def create_item(request: Request):
    json_post_raw = await request.json()
    query = json_post_raw.get("query")

    context = dict()
    context['question'] = query
    context["online_url_lists"] = []
    context["online_steps"] = []
    context["online_answer"] = ""
    context["online_code_results"] = []
    context["online_answer_stars"] = None
    

    queue = Queue()
    api_queue = WrapperQueue(queue)
    thread = threading.Thread(target=deepresearch_workflow.run, args=(query, WrapperQueue(), api_queue, LANGUAGE), kwargs={"context": context})
    thread.start()
    return StreamingResponse(generator(api_queue), media_type="text/event-stream")

@app.post("/v1/chat/completions")
async def create_item(request: Request):
    json_post_raw = await request.json()
    model = json_post_raw.get("model", "deepresearch")
    messages = json_post_raw.get("messages", [])
    temperature = json_post_raw.get("temperature", 0.7)
    max_tokens = json_post_raw.get("max_tokens", 2048)
    stream = json_post_raw.get("stream", False)

    user_content = ""
    for msg in messages:
        if msg["role"] == "system":
            system_content = msg["content"]
        elif msg["role"] == "user":
            user_content = msg["content"]


    context = dict()
    context['question'] = user_content
    context["online_url_lists"] = []
    context["online_steps"] = []
    context["online_answer"] = ""
    context["online_code_results"] = []
    context["online_answer_stars"] = None
    

    queue = Queue()
    api_queue = WrapperQueue(queue)
    # thread = threading.Thread(target=deepresearch_workflow.run, args=(user_content, WrapperQueue(), WrapperQueue(), LANGUAGE), kwargs={"context": context})
    # thread = threading.Thread(target=deepresearch_workflow.run, args=(user_content, WrapperQueue(), WrapperQueue(), LANGUAGE), kwargs={"context": context})
    r = deepresearch_workflow.run(user_content, WrapperQueue(), api_queue, LANGUAGE, context,save_jsonl_path="/Users/chenyao/Documents/DeepLiterature/src/logs/running_logs.jsonl")
    # thread.start()
    logging.info("r: ", r)
    return r
    # return StreamingResponse(generator(api_queue), media_type="text/event-stream")



# if __name__ == '__main__':
#     uvicorn.run(app, host='0.0.0.0', port=36668, workers=1, timeout_keep_alive=60)
if __name__ == "__main__":
    import datasets
    dataset=datasets.load_dataset('/Users/chenyao/Documents/DeepLiterature/data')
    queries=[]
    queries_idx=[]
    res_lst = []
    with open("/Users/chenyao/Documents/DeepLiterature/src/logs/smol_test.jsonl", "rb") as f:
        data = f.readlines()
    for i,line in enumerate(data):
        try:
            ans=json.loads(line.decode("utf-8"))['now_messages_ls']
            if not ans:
                queries.append(dataset['test'][i]['question'])
                queries_idx.append(i)
        except:
            queries.append(dataset['test'][i]['question'])
            queries_idx.append(i)
        
    import concurrent.futures

    def process_query(query):
        user_content = query
        context = dict()
        context['question'] = user_content
        context["online_url_lists"] = []
        context["online_steps"] = []
        context["online_answer"] = ""
        context["online_code_results"] = []
        context["online_answer_stars"] = None
        queue = Queue()
        api_queue = WrapperQueue(queue)
        res = deepresearch_workflow.planner_run(user_content, WrapperQueue(), api_queue, LANGUAGE, context, save_jsonl_path="/Users/chenyao/Documents/DeepLiterature/src/logs/running_logs.jsonl")
        return res

    with concurrent.futures.ThreadPoolExecutor(max_workers=24) as executor:
        # 创建请求任务并使用tqdm显示进度条，同时传递索引来保持顺序
        futures = {
            executor.submit(process_query, query): index
            for index, query in enumerate(queries)
        }
        res_lst = [None] * len(futures)
        # 等待所有任务完成并按照提交顺序收集结果
        for future in tqdm(
            concurrent.futures.as_completed(futures), total=len(futures)
        ):
            try:
                retries = 3  # 设置重试次数
                while retries > 0:
                    try:
                        result = future.result()
                        index = futures[future]  # 获取任务对应的索引
                        res_lst[index] = result  # 将结果存储到正确的位置
                        break  # 成功后退出重试循环
                    except Exception as e:
                        retries -= 1
                        if retries == 0:
                            index = futures[future]
                            res_lst[index] = None  # 如果重试失败，则存储None
                            logging.error(f"Query at index {index} failed after retries: {e}")
                        else:
                            logging.warning(f"Retrying query at index {futures[future]}: {e}")
            except Exception as e:
                index = futures[future]
                res_lst[index] = None  # 如果出错，则存储None
                logging.error(f"Unexpected error for query at index {index}: {e}")
    with open("/Users/chenyao/Documents/DeepLiterature/src/logs/smol_test_sample.pkl", "wb") as f:
        pickle.dump(res_lst, f)
    for i,idx in zip(range(len(queries)),queries_idx):
        data[idx]=json.loads(res_lst[i], ensure_ascii=False)
        
    with open("/Users/chenyao/Documents/DeepLiterature/src/logs/smol_test_n.jsonl", "w") as f:
        for res in data:
            f.write(json.dumps(res, ensure_ascii=False)+"\n")
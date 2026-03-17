#novel_generator/common.py
# -*- coding: utf-8 -*-
"""
通用重试、清洗、日志工具
"""
import logging
import re
import time
import signal
import traceback
import logging
import re

logging.basicConfig(
    filename='app.log',      # 日志文件名
    filemode='a',            # 追加模式（'w' 会覆盖）
    level=logging.INFO,      # 记录 INFO 及以上级别的日志
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class TimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutException("Function call timed out")

def call_with_retry(func, max_retries=3, sleep_time=2, fallback_return=None, timeout_seconds=None, **kwargs):
    """
    通用的重试机制封装，支持超时控制。
    :param func: 要执行的函数
    :param max_retries: 最大重试次数
    :param sleep_time: 重试前的等待秒数
    :param fallback_return: 如果多次重试仍失败时的返回值
    :param timeout_seconds: 超时秒数（可选）
    :param kwargs: 传给func的命名参数
    :return: func的结果，若失败则返回 fallback_return
    """
    for attempt in range(1, max_retries + 1):
        try:
            if timeout_seconds:
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(timeout_seconds)
            try:
                result = func(**kwargs)
                if timeout_seconds:
                    signal.alarm(0)
                return result
            finally:
                if timeout_seconds:
                    signal.alarm(0)
        except TimeoutException:
            logging.warning(f"[call_with_retry] Attempt {attempt} timed out after {timeout_seconds}s")
            if attempt < max_retries:
                time.sleep(sleep_time)
            else:
                logging.error("Max retries reached (timeout), returning fallback_return.")
                return fallback_return
        except Exception as e:
            logging.warning(f"[call_with_retry] Attempt {attempt} failed with error: {e}")
            traceback.print_exc()
            if attempt < max_retries:
                time.sleep(sleep_time)
            else:
                logging.error("Max retries reached, returning fallback_return.")
                return fallback_return

def remove_think_tags(text: str) -> str:
    """移除 <think>...</think> 包裹的内容"""
    return re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)

def debug_log(prompt: str, response_content: str):
    logging.info(
        f"\n[#########################################  Prompt  #########################################]\n{prompt}\n"
    )
    logging.info(
        f"\n[######################################### Response #########################################]\n{response_content}\n"
    )

def invoke_with_cleaning(llm_adapter, prompt: str, max_retries: int = 3, timeout_seconds: int = 300) -> str:
    """调用 LLM 并清理返回结果，支持超时控制"""
    import threading
    
    print("\n" + "="*50)
    print("发送到 LLM 的提示词:")
    print("-"*50)
    print(prompt)
    print("="*50 + "\n")
    
    result = ""
    retry_count = 0
    
    def invoke_with_timeout():
        nonlocal result
        result = llm_adapter.invoke(prompt)
    
    while retry_count < max_retries:
        result = ""
        invoke_thread = threading.Thread(target=invoke_with_timeout)
        invoke_thread.daemon = True
        invoke_thread.start()
        invoke_thread.join(timeout=timeout_seconds)
        
        if invoke_thread.is_alive():
            print(f"调用超时 ({retry_count + 1}/{max_retries}): 超过 {timeout_seconds} 秒")
            retry_count += 1
            continue
            
        try:
            print("\n" + "="*50)
            print("LLM 返回的内容:")
            print("-"*50)
            print(result)
            print("="*50 + "\n")
            
            result = result.replace("```", "").strip()
            if result:
                return result
            retry_count += 1
        except Exception as e:
            print(f"调用失败 ({retry_count + 1}/{max_retries}): {str(e)}")
            retry_count += 1
            if retry_count >= max_retries:
                raise e
    
    return result


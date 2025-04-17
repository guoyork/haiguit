import json
import requests
import time
from pathlib import Path

# 配置
OPENROUTER_API_KEY = "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"
MODEL = "deepseek/deepseek-chat-v3-0324"
PUZZLES_FILE = "puzzles/puzzles.json"
FOLLOWUPS_FILE = "puzzles/followups.json"
OUTPUT_FILE = "puzzles/answers.json"
MAX_RETRIES = 3
DELAY_BETWEEN_REQUESTS = 1  # 秒


def load_json_file(file_path):
    """加载JSON文件"""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json_file(data, file_path):
    """保存数据到JSON文件"""
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def call_openrouter_api(prompt, max_tokens=200):
    """调用OpenRouter API获取回答"""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens
    }

    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print(f"尝试 {attempt + 1} 失败: {str(e)}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(DELAY_BETWEEN_REQUESTS * (attempt + 1))
            else:
                raise


def generate_answers():
    """生成所有问题的答案"""
    # 加载数据
    puzzles = load_json_file(PUZZLES_FILE)
    followups = load_json_file(FOLLOWUPS_FILE)
    # 初始化结果结构
    results = {}
    count = 0
    # 处理每个谜题
    for puzzle in puzzles:
        count += 1
        # if count > 1:
        #     break
        puzzle_id = puzzle["filename"]
        if puzzle_id not in followups:
            continue

        print(f"处理谜题: {puzzle['title']}")
        results[puzzle_id] = {
            "title": puzzle["title"],
            "questions": []
        }

        # 处理每个问题
        for question in followups[puzzle_id]["try"]:
            # 构建提示
            prompt = f"""你是一个海龟汤游戏主持人，根据以下谜题回答问题：
谜题标题: {puzzle['title']}
谜题内容: {puzzle['question']}
谜题答案: {puzzle['answer']}

问题: {question}

回答规则:
1. 只返回以下四种格式之一，不要包含任何分析或其他文字:
   - "{{是}}"
   - "{{不是}}"
   - "{{是也不是}}"
   - "{{没有关系}}"
2. 如果问题部分正确回答"{{是也不是}}"
3. 如果问题与谜题无关回答"{{没有关系}}"

请只返回格式化的回答，不要包含任何其他内容:"""

            # 调用API
            try:
                answer = call_openrouter_api(prompt)
                results[puzzle_id]["questions"].append({
                    "question": question,
                    "answer": answer
                })
                print(f" - 已回答: {question}")
            except Exception as e:
                print(f" - 回答失败: {question} - {str(e)}")
                results[puzzle_id]["questions"].append({
                    "question": question,
                    "answer": "回答失败",
                    "error": str(e)
                })

            # 延迟防止速率限制
            time.sleep(DELAY_BETWEEN_REQUESTS)

    # 保存结果
        save_json_file(results, OUTPUT_FILE)
    print(f"所有问题已回答，结果已保存到 {OUTPUT_FILE}")


if __name__ == "__main__":
    generate_answers()

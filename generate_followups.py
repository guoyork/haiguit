import json
import requests
from typing import List

# OpenRouter配置
OPENROUTER_API_KEY = "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"
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "deepseek/deepseek-chat-v3-0324"


def load_puzzles(filepath: str) -> List[dict]:
    """加载海龟汤谜题数据"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_followup_questions(question: str, n=10) -> List[str]:
    """使用DeepSeek模型生成追问问题"""
    prompt = f"""请为以下海龟汤谜题生成{n}个可能的追问问题，帮助玩家思考：
谜题：{question}

要求：
1. 每个问题单独一行
2. 每个问题可以用是或否回答
3. 从不同角度提问
4. 逐步引导思考
5. 问题应该简洁明了"""

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": "你是一个海龟汤游戏助手，擅长生成引导性问题。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 1000
    }

    try:
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return [q.strip() for q in content.split("\n") if q.strip()][:n]
    except Exception as e:
        print(f"生成追问问题时出错: {e}")
        return [f"关于'{question}'的追问问题{i+1}" for i in range(n)]


def main():
    puzzles = load_puzzles('puzzles/puzzles.json')
    output = {}
    count = 0
    for puzzle in puzzles:
        count += 1
        # if count > 10:
        #     break
        questions = generate_followup_questions(puzzle['question'])
        output[puzzle['filename']] = {
            "try": questions
        }
        print(questions)

    with open('puzzles/followups.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"已为{len(puzzles)}个谜题生成追问问题，保存到puzzles/followups.json")


if __name__ == '__main__':
    main()

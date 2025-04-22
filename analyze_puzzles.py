from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import json
import os
from pathlib import Path


def load_model():
    model_name = "./Qwen2.5-7B-Instruct"
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")

    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16,
        use_flash_attention_2=False
    ).to(device)

    if device == "cuda":
        print("Model loaded on GPU")
    else:
        print("Warning: Using CPU - performance will be slower")

    return model, tokenizer


def extract_puzzle_content(file_path):
    """For .md files with Chinese puzzles"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 提取汤面部分(问题)
    start = content.find("### 汤面") + len("### 汤面")
    end = content.find("### 汤底")
    puzzle = content[start:end].strip()

    # 提取汤底部分(答案)
    start = content.find("### 汤底") + len("### 汤底")
    end = content.find("### 附加说明") if "### 附加说明" in content else len(content)
    answer = content[start:end].strip()

    return puzzle, answer


def extract_yesno_puzzle(json_path):
    """For yesno_puzzles.json with English puzzles"""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    puzzles = []
    for item in data:
        if isinstance(item, dict) and 'question' in item and 'answer' in item:
            puzzles.append((item['question'], item['answer']))
    return puzzles


def calculate_logprob(model, tokenizer, prompt, continuation):
    # 拼接提示和续写
    full_text = prompt + continuation
    inputs = tokenizer(full_text, return_tensors="pt").to(model.device)
    prompt_len = len(tokenizer.encode(prompt))

    with torch.no_grad():
        outputs = model(**inputs)

    logits = outputs.logits[0]
    probs = torch.nn.functional.log_softmax(logits, dim=-1)

    # 只计算continuation部分的logprob
    total_logprob = 0.0
    for i in range(prompt_len, len(inputs.input_ids[0])):
        token_id = inputs.input_ids[0][i]
        token_prob = probs[i-1, token_id].item()
        total_logprob += token_prob

    return total_logprob


def analyze_puzzle(model, tokenizer, puzzle_text, answer_text):
    # 计算基于汤面预测汤底的logprob
    answer_given_puzzle = calculate_logprob(model, tokenizer, puzzle_text, answer_text)

    # 计算基于汤底预测汤面的logprob
    puzzle_given_answer = calculate_logprob(model, tokenizer, answer_text, puzzle_text)

    # 计算无提示时生成答案的logprob
    answer_given_empty = calculate_logprob(model, tokenizer, "", answer_text)

    # 计算无提示时生成问题的logprob
    puzzle_given_empty = calculate_logprob(model, tokenizer, "", puzzle_text)

    return {
        "answer_given_puzzle": answer_given_puzzle,
        "puzzle_given_answer": puzzle_given_answer,
        "answer_given_empty": answer_given_empty,
        "puzzle_given_empty": puzzle_given_empty,
        "answer_prompt_effect": answer_given_puzzle - answer_given_empty,
        "puzzle_prompt_effect": puzzle_given_answer - puzzle_given_empty
    }


def process_all_puzzles():
    """Process Chinese puzzles from .md files"""
    model, tokenizer = load_model()
    puzzle_files = [f for f in os.listdir('puzzles') if f.endswith('.md')]

    results = []
    total_answer_given_puzzle = 0.0
    total_puzzle_given_answer = 0.0

    for puzzle_file in puzzle_files:
        file_path = Path('puzzles') / puzzle_file
        puzzle_text, answer_text = extract_puzzle_content(file_path)

        analysis = analyze_puzzle(model, tokenizer, puzzle_text, answer_text)
        total_answer_given_puzzle += analysis["answer_given_puzzle"]
        total_puzzle_given_answer += analysis["puzzle_given_answer"]

        results.append({
            "file": puzzle_file,
            "puzzle_text": puzzle_text,
            "answer_text": answer_text,
            "logprobs": analysis
        })
        print(analysis)

    # 计算统计信息
    num_puzzles = len(results)
    stats = {
        "total_answer_given_puzzle": total_answer_given_puzzle,
        "total_puzzle_given_answer": total_puzzle_given_answer,
        "avg_answer_given_puzzle": total_answer_given_puzzle / num_puzzles,
        "avg_puzzle_given_answer": total_puzzle_given_answer / num_puzzles
    }

    # 保存结果到JSON文件
    output = {
        "puzzles": results,
        "statistics": stats
    }

    with open('puzzle_logprobs.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print("分析完成，结果已保存到 puzzle_logprobs.json")


def process_yesno_puzzles():
    """Process English puzzles from yesno_puzzles.json incrementally"""
    model, tokenizer = load_model()
    puzzle_pairs = extract_yesno_puzzle('yesno_puzzles.json')

    # Load existing results if file exists
    output_file = 'yesno_puzzle_logprobs.json'
    if os.path.exists(output_file):
        with open(output_file, 'r', encoding='utf-8') as f:
            output = json.load(f)
        existing_ids = {p['id'] for p in output['puzzles']}
    else:
        output = {"puzzles": [], "statistics": {}}
        existing_ids = set()

    # Initialize totals from existing results
    total_answer_given_puzzle = sum(p['logprobs']['answer_given_puzzle']
                                    for p in output['puzzles'])
    total_puzzle_given_answer = sum(p['logprobs']['puzzle_given_answer']
                                    for p in output['puzzles'])

    # Process only new puzzles
    new_count = 0
    for idx, (puzzle_text, answer_text) in enumerate(puzzle_pairs):
        if idx in existing_ids:
            continue

        analysis = analyze_puzzle(model, tokenizer, puzzle_text, answer_text)
        total_answer_given_puzzle += analysis["answer_given_puzzle"]
        total_puzzle_given_answer += analysis["puzzle_given_answer"]

        output['puzzles'].append({
            "id": idx,
            "puzzle_text": puzzle_text,
            "answer_text": answer_text,
            "logprobs": analysis
        })
        new_count += 1
        print(f"Processed puzzle {idx}: {analysis}")

        # Save after each new puzzle
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

    # Update statistics
    num_puzzles = len(output['puzzles'])
    output['statistics'] = {
        "total_answer_given_puzzle": total_answer_given_puzzle,
        "total_puzzle_given_answer": total_puzzle_given_answer,
        "avg_answer_given_puzzle": total_answer_given_puzzle / num_puzzles,
        "avg_puzzle_given_answer": total_puzzle_given_answer / num_puzzles
    }

    # Final save
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"Processed {new_count} new puzzles. Total puzzles: {num_puzzles}")
    print(f"Results saved to {output_file}")


if __name__ == "__main__":
    # model, tokenizer = load_model()
    # process_all_puzzles()  # For Chinese puzzles
    process_yesno_puzzles()  # For English puzzles

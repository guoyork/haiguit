import os
import re
import json


def extract_puzzle_content(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 更健壮的正则表达式匹配
    patterns = {
        'question': r'### 汤面\s*\n+([\s\S]+?)\s*(?=\n### 汤底|\Z)',
        'answer': r'### 汤底\s*\n+([\s\S]+?)\s*(?=\n### 附加说明|\Z)',
        'note': r'### 附加说明\s*\n+([\s\S]+)'
    }

    result = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, content)
        result[key] = match.group(1).strip() if match else '无附加说明' if key == 'note' else '内容缺失'

    # 验证必填字段
    if result['question'] == '内容缺失' or result['answer'] == '内容缺失':
        print(f"警告: {filepath} 缺少必要字段")

    return result


def main():
    puzzles = []
    puzzle_dir = 'puzzles'

    for filename in os.listdir(puzzle_dir):
        if filename.endswith('.md'):
            filepath = os.path.join(puzzle_dir, filename)
            puzzle_data = extract_puzzle_content(filepath)

            puzzles.append({
                'filename': filename,
                'title': filename[:-3],  # 去掉.md后缀
                'question': puzzle_data['question'],
                'answer': puzzle_data['answer'],
                'note': puzzle_data['note']
            })

    # 写入JSON文件
    with open(os.path.join(puzzle_dir, 'puzzles.json'), 'w', encoding='utf-8') as f:
        json.dump(puzzles, f, ensure_ascii=False, indent=2)

    print(f"成功处理{len(puzzles)}个谜题，已保存到puzzles/puzzles.json")


if __name__ == '__main__':
    main()

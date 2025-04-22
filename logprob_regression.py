import json
import matplotlib.pyplot as plt
from scipy import stats
import numpy as np

# 读取JSON文件
with open('yesno_puzzle_logprobs.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 提取数据
puzzles = data['puzzles']

# 准备数据
puzzle_lengths = []
puzzle_logprobs = []
puzzle_prompt_effects = []
answer_lengths = []
answer_logprobs = []
answer_prompt_effects = []

for puzzle in puzzles:
    # Puzzle回归数据
    puzzle_text = puzzle['puzzle_text']
    puzzle_lengths.append(len(puzzle_text))
    puzzle_logprobs.append(puzzle['logprobs']['puzzle_given_answer'])
    puzzle_prompt_effects.append(puzzle['logprobs']['puzzle_prompt_effect'])

    # Answer回归数据
    answer_text = puzzle['answer_text']
    answer_lengths.append(len(answer_text))
    answer_logprobs.append(puzzle['logprobs']['answer_given_puzzle'])
    answer_prompt_effects.append(puzzle['logprobs']['answer_prompt_effect'])

# 转换为numpy数组
puzzle_lengths = np.array(puzzle_lengths)
puzzle_logprobs = np.array(puzzle_logprobs)
puzzle_prompt_effects = np.array(puzzle_prompt_effects)
answer_lengths = np.array(answer_lengths)
answer_logprobs = np.array(answer_logprobs)
answer_prompt_effects = np.array(answer_prompt_effects)

# Puzzle回归分析
puzzle_slope, puzzle_intercept, puzzle_r_value, puzzle_p_value, puzzle_std_err = stats.linregress(
    puzzle_lengths, puzzle_logprobs)
puzzle_line = puzzle_slope * puzzle_lengths + puzzle_intercept

# Answer回归分析
answer_slope, answer_intercept, answer_r_value, answer_p_value, answer_std_err = stats.linregress(
    answer_lengths, answer_logprobs)
answer_line = answer_slope * answer_lengths + answer_intercept

# Answer Prompt Effect回归分析
answer_effect_slope, answer_effect_intercept, answer_effect_r_value, answer_effect_p_value, answer_effect_std_err = stats.linregress(
    answer_lengths, answer_prompt_effects)
answer_effect_line = answer_effect_slope * answer_lengths + answer_effect_intercept

# Puzzle Prompt Effect回归分析
puzzle_effect_slope, puzzle_effect_intercept, puzzle_effect_r_value, puzzle_effect_p_value, puzzle_effect_std_err = stats.linregress(
    puzzle_lengths, puzzle_prompt_effects)
puzzle_effect_line = puzzle_effect_slope * puzzle_lengths + puzzle_effect_intercept

# 绘制图表
plt.figure(figsize=(18, 12))

# Puzzle回归图
plt.subplot(2, 2, 1)
plt.scatter(puzzle_lengths, puzzle_logprobs, alpha=0.5, label='Data points')
plt.plot(puzzle_lengths, puzzle_line, 'r', label=f'Regression line (R²={puzzle_r_value**2:.2f})')
plt.xlabel('Puzzle Text Length')
plt.ylabel('Puzzle Given Answer Logprob')
plt.title('Puzzle Text Length vs Logprob')
plt.legend()

# Answer回归图
plt.subplot(2, 2, 2)
plt.scatter(answer_lengths, answer_logprobs, alpha=0.5, label='Data points')
plt.plot(answer_lengths, answer_line, 'r', label=f'Regression line (R²={answer_r_value**2:.2f})')
plt.xlabel('Answer Text Length')
plt.ylabel('Answer Given Puzzle Logprob')
plt.title('Answer Text Length vs Logprob')
plt.legend()

# Answer Prompt Effect回归图
plt.subplot(2, 2, 3)
plt.scatter(answer_lengths, answer_prompt_effects, alpha=0.5, label='Data points')
plt.plot(answer_lengths, answer_effect_line, 'r', label=f'Regression line (R²={answer_effect_r_value**2:.2f})')
plt.xlabel('Answer Text Length')
plt.ylabel('Answer Prompt Effect')
plt.title('Answer Length vs Prompt Effect')
plt.legend()

# Puzzle Prompt Effect回归图
plt.subplot(2, 2, 4)
plt.scatter(puzzle_lengths, puzzle_prompt_effects, alpha=0.5, label='Data points')
plt.plot(puzzle_lengths, puzzle_effect_line, 'r', label=f'Regression line (R²={puzzle_effect_r_value**2:.2f})')
plt.xlabel('Puzzle Text Length')
plt.ylabel('Puzzle Prompt Effect')
plt.title('Puzzle Length vs Prompt Effect')
plt.legend()

plt.tight_layout()
plt.savefig('logprob_regression.png')
plt.show()

# 打印回归结果
print("Puzzle Regression Results:")
print(f"Slope: {puzzle_slope:.4f}, Intercept: {puzzle_intercept:.4f}")
print(f"R-squared: {puzzle_r_value**2:.4f}, p-value: {puzzle_p_value:.4g}")

print("\nAnswer Regression Results:")
print(f"Slope: {answer_slope:.4f}, Intercept: {answer_intercept:.4f}")
print(f"R-squared: {answer_r_value**2:.4f}, p-value: {answer_p_value:.4g}")

print("\nAnswer Prompt Effect Regression Results:")
print(f"Slope: {answer_effect_slope:.4f}, Intercept: {answer_effect_intercept:.4f}")
print(f"R-squared: {answer_effect_r_value**2:.4f}, p-value: {answer_effect_p_value:.4g}")

print("\nPuzzle Prompt Effect Regression Results:")
print(f"Slope: {puzzle_effect_slope:.4f}, Intercept: {puzzle_effect_intercept:.4f}")
print(f"R-squared: {puzzle_effect_r_value**2:.4f}, p-value: {puzzle_effect_p_value:.4g}")

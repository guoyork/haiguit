import json


def calculate_and_sort_puzzles(input_file, output_file):
    """
    Calculate answer_given_puzzle - puzzle_given_answer for each puzzle,
    sort by this value, and save to new JSON file with calculated values.
    """
    try:
        # Read input JSON file
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Process each puzzle
        puzzles = data['puzzles']
        for puzzle in puzzles:
            # Calculate the metric
            answer_puzzle = puzzle['logprobs']['answer_given_puzzle']
            answer_given_empty = puzzle['logprobs']['answer_given_empty']
            puzzle['calculated_value'] = answer_puzzle - answer_given_empty

        # Sort puzzles by calculated_value
        sorted_puzzles = sorted(puzzles, key=lambda x: x['calculated_value'])

        # Create output structure
        output_data = {
            "sorted_puzzles": sorted_puzzles,
            "statistics": {
                "min_value": min(p['calculated_value'] for p in sorted_puzzles),
                "max_value": max(p['calculated_value'] for p in sorted_puzzles),
                "avg_value": sum(p['calculated_value'] for p in sorted_puzzles)/len(sorted_puzzles)
            }
        }

        # Save to output file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        print(f"Successfully sorted and saved puzzles to {output_file}")

    except Exception as e:
        print(f"Error processing puzzles: {str(e)}")


if __name__ == "__main__":
    input_file = "puzzles/puzzle_logprobs.json"
    output_file = "puzzles/sorted_puzzles.json"
    calculate_and_sort_puzzles(input_file, output_file)

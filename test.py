import json
import requests

# Load puzzles from JSON file

# OpenRouter API settings
OPENROUTER_API_KEY = "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"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "deepseek/deepseek-chat-v3-0324"
with open('yesno_puzzles.json', 'r', encoding='utf-8') as f:
    puzzles = json.load(f)


def generate_endings_with_openrouter(begin_text, num_endings=10):
    """Generate possible endings using OpenRouter API"""
    endings = []
    prompt = f"""Given the beginning of a story, generate {num_endings} possible endings.
Each ending should be one complete sentence start with a serial number.

Example:
Begin: xxxx
Endings:
1. xxxx
2. xxxx
3. xxxx

Now generate endings for:
Begin: {begin_text}
Endings:
"""

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 50 * num_endings
    }

    try:
        response = requests.post(OPENROUTER_URL, headers=headers, json=data)
        response.raise_for_status()
        content = response.json()['choices'][0]['message']['content']

        # Parse generated endings
        endings = [line.strip() for line in content.split("\n")
                   if line.strip() and line[0].isdigit()]
        return endings[:num_endings]
    except Exception as e:
        print(f"Error calling OpenRouter API: {e}")
        return []


def generate_endings():
    # Load puzzles and generate endings using OpenRouter
    try:
        with open('rewritten_puzzles.json', 'r', encoding='utf-8') as f:
            puzzles = json.load(f)

        count = 0
        # Generate endings for each puzzle
        for puzzle in puzzles:
            # if count > 10:
            #     break
            # count += 1
            if 'begin_text' in puzzle and 'end_text' in puzzle:
                print(f"Generating endings for: {puzzle['begin_text']}")
                puzzle['generated_endings'] = generate_endings_with_openrouter(puzzle['begin_text'])

        # Save with generated endings
        with open('generated_endings.json', 'w', encoding='utf-8') as f:
            json.dump(puzzles, f, ensure_ascii=False, indent=2)

        print("Endings generation complete using OpenRouter API. Saved to generated_endings.json")

    except Exception as e:
        print(f"Error processing puzzles: {e}")


def begin_ending_prob(begin_text, end_text, generated_endings):
    # Prepare prompt for probability calculation
    prompt = f"""Given the beginning of a story, predict the probability of each possible ending only based on the logic of the story.
        Begin: {begin_text}
        Possible endings:
        """
    for i, ending in enumerate(generated_endings, 1):
        prompt += f"{i}. {ending}\n"
    prompt += f"{len(generated_endings)+1}. {end_text}\n\n"
    prompt += "You should first provide reasons and return a single list of numbers between 0 and 1 as the probabilities at the end."

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 100*len(generated_endings),
        "logprobs": True
    }

    max_retries = 3
    probs = None

    for attempt in range(max_retries):
        try:
            response = requests.post(OPENROUTER_URL, headers=headers, json=data)
            response.raise_for_status()
            content = response.json()['choices'][0]['message']['content']
            print(content)

            # Try to extract probability vector from any line
            for line in content.strip().split('\n'):
                line = line.strip()
                if line.startswith('[') and line.endswith(']'):
                    try:
                        probs = json.loads(line)
                        if len(probs) == len(generated_endings) + 1:
                            print("Successfully parsed probability vector from response")
                            break
                        else:
                            raise ValueError("Probability vector length mismatch")
                    except json.JSONDecodeError:
                        continue
            else:
                raise ValueError("No probability vector found in response")

        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                print("Retrying...")

        if probs != None:
            return probs

    return None


def calculate_probs():
    """Calculate probabilities for generated endings and true endings"""
    try:
        with open('generated_endings.json', 'r', encoding='utf-8') as f:
            puzzles = json.load(f)

        results = []

        for puzzle in puzzles:
            if 'begin_text' not in puzzle or 'end_text' not in puzzle or 'generated_endings' not in puzzle:
                continue

            begin_text = puzzle['begin_text']
            end_text = puzzle['end_text']
            generated_endings = puzzle['generated_endings']

            probs = begin_ending_prob(begin_text, end_text, generate_endings)
            # Use fallback if all attempts failed
            if probs is None:
                print(f"Failed to get valid probability vector.")
                probs = [1.0 / (len(generated_endings) + 1)] * (len(generated_endings) + 1)

            results.append({
                "begin_text": begin_text,
                "probs": probs,
                "generated_endings": generated_endings,
                "end_text": end_text
            })

            print(f"Calculated probabilities for: {begin_text}")
            print(f"Probability vector: {probs}")

            # Save results
            with open('ending_probs.json', 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)

        print("Probability calculation complete. Saved to ending_probs.json")
        return results

    except Exception as e:
        print(f"Error in calculate_probs: {e}")
        return None


def begin_back_end_probs(begin_text, end_text, back_text, generated_endings):
    # Prepare prompt for probability calculation
    prompt = f"""Given the beginning and background of a story, predict the probability of each possible ending only based on the logic of the story.
        Beginning: {begin_text}
        Background: {back_text}
        Possible endings:
        """
    for i, ending in enumerate(generated_endings, 1):
        prompt += f"{i}. {ending}\n"
    prompt += f"{len(generated_endings)+1}. {end_text}\n\n"
    prompt += "You should first provide reasons and return a single list of numbers between 0 and 1 as the probabilities at the end."

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 100*len(generated_endings),
        "logprobs": True
    }

    max_retries = 3
    probs = None

    for attempt in range(max_retries):
        try:
            response = requests.post(OPENROUTER_URL, headers=headers, json=data)
            response.raise_for_status()
            content = response.json()['choices'][0]['message']['content']
            print(content)

            # Try to extract probability vector from any line
            for line in content.strip().split('\n'):
                line = line.strip()
                if line.startswith('[') and line.endswith(']'):
                    try:
                        probs = json.loads(line)
                        if len(probs) == len(generated_endings) + 1:
                            print("Successfully parsed probability vector from response")
                            break
                        else:
                            raise ValueError("Probability vector length mismatch")
                    except json.JSONDecodeError:
                        continue
            else:
                raise ValueError("No probability vector found in response")

        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                print("Retrying...")

        if probs != None:
            return probs

    return None


def calculate_probs2():
    """Calculate probabilities for generated endings and true endings"""
    try:
        with open('generated_endings.json', 'r', encoding='utf-8') as f:
            puzzles = json.load(f)

        results = []

        for puzzle in puzzles:
            if 'begin_text' not in puzzle or 'end_text' not in puzzle or 'generated_endings' not in puzzle:
                continue
            if puzzle['title'] != "Open the door!":
                continue
            begin_text = puzzle['begin_text']
            end_text = puzzle['end_text']
            back_text = puzzle['answer']
            generated_endings = puzzle['generated_endings']

            probs = begin_back_end_probs(begin_text, end_text, back_text, generate_endings)

            # Use fallback if all attempts failed
            if probs is None:
                print(f"Failed to get valid probability vector")
                probs = [1.0 / (len(generated_endings) + 1)] * (len(generated_endings) + 1)

            results.append({
                "begin_text": begin_text,
                "probs": probs,
                "generated_endings": generated_endings,
                "end_text": end_text
            })

            print(f"Calculated probabilities for: {begin_text}")
            print(f"Probability vector: {probs}")

            # Save results
            with open('ending_probs2.json', 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)

        print("Probability calculation complete. Saved to ending_probs.json")
        return results

    except Exception as e:
        print(f"Error in calculate_probs: {e}")
        return None


def generate_explanations_with_openrouter(begin_text, end_text, num_explanations=10):
    """Generate possible explanations using OpenRouter API"""
    explanations = []
    prompt = f"""Given the beginning and ending of a story, generate {num_explanations} possible explanations for how the beginning leads to the ending.
Each explanation should be one complete sentence start with a serial number.

Example:
Begin: xxxx
Endings:
1. xxxx
2. xxxx
3. xxxx

Now generate explanations for:
Begin: {begin_text}
End: {end_text}
Explanations:
"""

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 50 * num_explanations
    }

    try:
        response = requests.post(OPENROUTER_URL, headers=headers, json=data)
        response.raise_for_status()
        content = response.json()['choices'][0]['message']['content']

        # Parse generated explanations
        explanations = [line.strip() for line in content.split("\n")
                        if line.strip() and line[0].isdigit()]
        return explanations[:num_explanations]
    except Exception as e:
        print(f"Error calling OpenRouter API: {e}")
        return []


def generate_explanations():
    """Generate explanations for puzzles in generated_endings.json"""
    try:
        with open('generated_endings.json', 'r', encoding='utf-8') as f:
            puzzles = json.load(f)

        count = 0
        for puzzle in puzzles:
            # if count > 10:
            #     break
            # count += 1
            if 'begin_text' in puzzle and 'end_text' in puzzle:
                print(f"Generating endings for: {puzzle['begin_text']}")
                puzzle['generated_explainations'] = generate_explanations_with_openrouter(
                    puzzle['begin_text'], puzzle['end_text'])

        # Save with generated endings
        with open('generated_explainations.json', 'w', encoding='utf-8') as f:
            json.dump(puzzles, f, ensure_ascii=False, indent=2)

        print("Endings generation complete using OpenRouter API. Saved to generated_explainations.json")

    except Exception as e:
        print(f"Error processing puzzles: {e}")


def begin_explanation_prob(begin_text, end_text, generated_explanations, answer):
    """Calculate probabilities for generated explanations using OpenRouter API"""
    prompt = f"""Given the beginning and ending of a story, predict the probability of each explainations.
        Begin: {begin_text}
        End: {end_text}
        Explainations:
        """
    for i, explanation in enumerate(generated_explanations, 1):
        prompt += f"{i}. {explanation}\n"
    prompt += f"{len(generated_explanations)+1}. {answer}\n\n"
    prompt += "You should first provide reasons and return a single list of numbers between 0 and 1 as the probabilities at the end."

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 100 * len(generated_explanations)
    }

    max_retries = 3
    probs = None

    for attempt in range(max_retries):
        try:
            response = requests.post(OPENROUTER_URL, headers=headers, json=data)
            response.raise_for_status()
            content = response.json()['choices'][0]['message']['content']
            print(content)

            # Try to extract probability vector from any line
            for line in content.strip().split('\n'):
                line = line.strip()
                if line.startswith('[') and line.endswith(']'):
                    try:
                        probs = json.loads(line)
                        if len(probs) == len(generated_explanations) + 1:
                            print("Successfully parsed probability vector from response")
                            break
                        else:
                            raise ValueError("Probability vector length mismatch")
                    except json.JSONDecodeError:
                        continue
            else:
                raise ValueError("No probability vector found in response")

        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                print("Retrying...")

        if probs != None:
            return probs

    return None


def calculate_explanation_probs():
    """Calculate probabilities for generated explanations and true answers"""
    try:
        with open('generated_explanations.json', 'r', encoding='utf-8') as f:
            puzzles = json.load(f)

        results = []

        for puzzle in puzzles:
            if 'begin_text' not in puzzle or 'end_text' not in puzzle or 'generated_explanations' not in puzzle:
                continue

            begin_text = puzzle['begin_text']
            end_text = puzzle['end_text']
            generated_explanations = puzzle['generated_explanations']
            answer = puzzle['answer']

            print(f"Calculating probabilities for: {begin_text}")
            probs = begin_explanation_prob(begin_text, end_text, generated_explanations, answer)

            results.append({
                "begin_text": begin_text,
                "end_text": end_text,
                "generated_explanations": generated_explanations,
                "explanation_probs": probs,
                "answer": answer
            })

            print(f"Probability vector: {probs}")

        # Save results
        with open('explanation_probs.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print("Explanation probability calculation complete. Saved to explanation_probs.json")
        return results

    except Exception as e:
        print(f"Error in calculate_explanation_probs: {e}")
        return None


# Calculate and save probabilities
if __name__ == "__main__":
    begin_text = "Three ducklings are swimming in the lake in a row.\r\n\r\nThe first duckling says, “There are two ducklings swimming behind me.”\r\nThe second duckling says, “There is one duckling swimming in front of me, and another duckling is swimming behind me.” \r\n"
    end_text = "The third duckling says, “There are two ducklings swimming in front of me, and another one is swimming behind me.”\r\n"
    answer = "The third duckling lied."

    begin_text = "There is a mass buying up of salt in the whole city."
    end_text = "The cadets became the cause."
    answer = "Cadets were supposed to shovel the snow. But they were lazy so they strew the ground with salt. They bought lots of salt to perfrom it. When old people saw military men buying lots of salt, they thought there'll be a war soon and began to wreak havoc and buy up salt."

    begin_text = "A man was born in 1972 and dies in 1952."
    end_text = "He dies at the age of 25."
    answer = "He's born in room number 1972 of a hospital and dies in room number 1952."

    a = generate_explanations_with_openrouter(begin_text, end_text)

    # generate_endings()
    # calculate_probs()
    # calculate_probs2()
    # generate_explanations()

    #print(begin_ending_prob(begin_text, end_text, endings))
    # generate_explanations()
    # calculate_explanation_probs()
    begin_explanation_prob(begin_text, end_text, a, answer)

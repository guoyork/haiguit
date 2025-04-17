import requests
from bs4 import BeautifulSoup
import json
import time
import re

def get_puzzle_answer(puzzle_url):
    try:
        response = requests.get(puzzle_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find answer section
        answer_div = soup.select('.quest__story__text')[1]
        print(answer_div)
        if answer_div:
            return answer_div.text.strip()
        return "Answer not found"
    except Exception as e:
        print(f"Error scraping answer from {puzzle_url}: {e}")
        return "Error getting answer"

def scrape_yesno_puzzles():
    base_url = "https://yesnogame.net/en"
    all_puzzles = []
    
    for page in range(1, 21):  # Pages 1 through 20
        url = f"{base_url}?page={page}"
        print(f"Scraping page {page}...")
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all puzzle elements
            puzzle_elements = soup.select('.catalog__item')
            
            for puzzle in puzzle_elements:
                title = puzzle.select_one('.quest__title').text.strip()
                question = puzzle.select_one('.quest__story_question').text.strip()
                rating_div = puzzle.find('div', class_='quest__about')
                rating = rating_div.find('div', class_='quest__about__value').text.strip() if rating_div else 'N/A'
                
                # Extract puzzle ID from link
                puzzle_link = puzzle.find('a', href=True)['href']
                puzzle_id = re.search(r'/stories/(\d+)', puzzle_link)
                if puzzle_id:
                    puzzle_id = puzzle_id.group(1)
                    puzzle_url = f"{base_url}/stories/{puzzle_id}"
                    answer = get_puzzle_answer(puzzle_url)
                else:
                    answer = "Could not find puzzle ID"
                
                all_puzzles.append({
                    'title': title,
                    'question': question,
                    'rating': rating,
                    'answer': answer,
                    'url': puzzle_url if puzzle_id else "N/A"
                })
                
                # Be polite - add delay between requests
                time.sleep(1)
            
        except Exception as e:
            print(f"Error scraping page {page}: {e}")
            continue
    
    # Save all puzzles to JSON file
    with open('yesno_puzzles.json', 'w', encoding='utf-8') as f:
        json.dump(all_puzzles, f, ensure_ascii=False, indent=2)
    
    print(f"Scraped {len(all_puzzles)} puzzles with answers from 20 pages")

if __name__ == "__main__":
    scrape_yesno_puzzles()

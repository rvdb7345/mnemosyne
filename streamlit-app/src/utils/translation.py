import openai
import os

# Set your OpenAI API key
openai.api_key = "your_openai_api_key"

# File paths
input_file_path = "woorden.txt"
output_file_path = "woorden_with_articles.txt"

# Function to generate a prompt for determining the article
def generate_prompt(word):
    return f"""What is the correct Dutch article ("de" or "het") for the noun "{word}"? 
If "{word}" is not a noun or doesn't need an article, respond with "no article"."""


# Function to get the article using OpenAI's API
def get_article(word):
    prompt = generate_prompt(word)
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=10,
        )
        result = response.choices[0].message.content.strip().lower()
        if result in ["de", "het"]:
            return result
        return "no article"
    except Exception as e:
        print(f"Error processing word '{word}': {e}")
        return "error"

# Process the input file
with open(input_file_path, "r", encoding="utf-8") as input_file:
    lines = input_file.readlines()

updated_lines = []
for line in lines:
    word, *translations = line.split("\t")
    article = get_article(word)
    if article != "no article":
        updated_line = f"{article} {word}\t{'\t'.join(translations)}"
    else:
        updated_line = line  # Leave as is if no article is needed
    updated_lines.append(updated_line)

# Save the updated word list
with open(output_file_path, "w", encoding="utf-8") as output_file:
    output_file.writelines(updated_lines)

print(f"Updated file saved to {output_file_path}")

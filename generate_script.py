import os
import re
from dotenv import load_dotenv

load_dotenv()

# === Set environment variables to suppress warnings ===
os.environ['GRPC_VERBOSITY'] = 'NONE' # Suppress gRPC logs
os.environ['GLOG_minloglevel'] = '3' # Suppress glog logs (3 = FATAL)

# === Initialize absl logging to suppress warnings ===
import absl.logging
absl.logging.set_verbosity('error')
absl.logging.use_absl_handler()

# === Import other modules after setting environment variables ===
import google.generativeai as genai
import PyPDF2
import requests
from bs4 import BeautifulSoup

# === Rest of your code ===
def read_pdf(pdf_file): # Changed to accept file object
    try:
        reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted
        return text
    except Exception as e:
        print(f"Error reading PDF file: {str(e)}")
        return ""

def read_md(md_file): # Changed to accept file object
    try:
        return md_file.read().decode('utf-8') # Decode bytes to string
    except Exception as e:
        print(f"Error reading Markdown file: {str(e)}")
        return ""

def read_url(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup.get_text()
    except requests.exceptions.RequestException as e:
        print(f"Error accessing URL: {str(e)}")
        return ""
    except Exception as e:
        print(f"Error processing URL content: {str(e)}")
        return ""

def read_txt(txt_file): # Changed to accept file object
    try:
        return txt_file.read().decode('utf-8') # Decode bytes to string
    except Exception as e:
        print(f"Error reading text file: {str(e)}")
        return ""

def load_prompt_template():
    try:
        with open('system_instructions_script.txt', 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        raise FileNotFoundError("Prompt template file not found in system_instructions_script.txt")

def create_podcast_script(content):
    try:
        # Initialize Gemini
        genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
        model = genai.GenerativeModel('gemini-2.0-flash-exp')

        # Load prompt template and format with content
        prompt_template = load_prompt_template()
        prompt = f"{prompt_template}\n\nContent: {content}"

        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error generating content: {str(e)}")
        return None

def clean_podcast_script(script):
    # Define a regex pattern to identify the start of the podcast text
    podcast_start_pattern = r"^(Speaker A:|Speaker B:)"

    # Split the script into lines
    lines = script.splitlines()

    # Find the first line that matches the podcast start pattern
    for i, line in enumerate(lines):
        if re.match(podcast_start_pattern, line):
            # Return the script starting from the first podcast line
            return '\n'.join(lines[i:])

    # If no match is found, return the original script
    return script

if __name__ == "__main__":
    # This block will not be executed when imported as a module
    pass
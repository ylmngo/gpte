import argparse 
import os 
import re
import shutil
from typing import Any   
from dotenv import load_dotenv
import google.generativeai as genai
from google.ai.generativelanguage import Content, Part

def parse_arguements(): 
    parser = argparse.ArgumentParser(description="Configuration for the Prompts")
    parser.add_argument('--prompt', nargs=1, type=str, help="Location of the prompts file")
    parser.add_argument('--env', nargs=1, type=str, help="Location of .env file")
    parser.add_argument('--app', nargs=1, type=str, help="Name of the application")
    args = parser.parse_args()
    for flag, arg in args._get_kwargs(): 
        if arg == None: 
            print(f"{flag} is not set")
            exit(1)
        if flag == "prompt": 
            prompt_path = arg[0] 
        else: 
            env_path = arg[0] 
    return prompt_path, env_path, 

def load_api_key(path: str): 
    load_dotenv(dotenv_path=path) 
    key = os.getenv("API_ACCESS_KEY")
    if key == None: 
        print("API_ACCESS_KEY not found")
        exit(1)
    return key 

def read_prompts(path: str): 
    with open(path, 'r') as f: 
        prompts = f.read().split('\n') 
        if len(prompts) == 0: 
            print("NO PROMPTS FOUND IN PROMPTS FILE")
            exit(1) 
        for i in range(len(prompts)): 
            prompts[i] = prompts[i].rstrip()
    return prompts 

def parse_response(response: str) -> dict: 
    regex = r"(\S+)\n\s*```(\w*)[^\n]*\n(.+?)```"
    matches = re.finditer(regex, response, re.DOTALL)
    block_map = {}
    ctr = 0 
    for match in matches: 
        file_name = match.group(1)
        file_name = sanitize_name(file_name, match.group(2), ctr + 1)
        code_block = match.groups() 
        block_map[file_name] = code_block
        ctr += 1
    return block_map

def create_file_from_block(file_name: str, block: tuple[str | Any, ...]): 
    lang, code = block[1], block[2] 
    idx = file_name.rfind('/') 
    if idx != -1: 
        dir_name = file_name[:idx]
        os.makedirs(dir_name, exist_ok=True)
    with open(file_name, "w") as f: 
        f.write(code)
    return 
    
def sanitize_name(name: str, lang: str, ctr: int): 
    regex = r"\**(\S+?\.\w+)"
    matches = re.finditer(regex, name, re.DOTALL)
    for match in matches: 
        return 'app/'+match.group(1)
    match lang: 
        case 'python', 'py', 'python3': 
            file_name = f'python_{ctr}.py'
        case 'javascript', 'js': 
            file_name = f'javascript_{ctr}.js'
        case 'html', 'HTML': 
            file_name = f'HTML_{ctr}.html'
        case 'CSS', 'css': 
            file_name = f'CSS_{ctr}.css'
        case _: 
            file_name = f'text_file_{ctr}.txt'
    return 'app/'+file_name 

def create_proj(block_map: dict): 
    for k, v in block_map.items(): 
        create_file_from_block(k, v)


def compress_folder(zip_dir: str): 
    root_dir = os.getcwd() 
    base_name = os.path.join(root_dir, zip_dir)
    shutil.make_archive(base_name, 'zip', root_dir, zip_dir)

    
def run(): 
    prompt_path, env_path = parse_arguements() 
    api_key = load_api_key(env_path)
    os.makedirs('app/', exist_ok=True)
    begin = '''You will be asked to generate code for an application, your reply should include the necessary code blocks and the names of the files at the top: 
               Your reply should be structured as follows: 
               Name of the file: <name-of-the-file>.extension
               {Code Block}. 
            '''
    prompts = read_prompts(prompt_path)
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-pro')
    inp = ". ".join(prompts)
    for i in range(5): 
        response = model.generate_content(begin + inp+". Mention only the code blocks and the name of the file at the top of the code block")
        try: 
            block_map = parse_response(response=response.text)
        except ValueError: 
            continue 
        break 
    create_proj(block_map=block_map)
    compress_folder('app')
    
if __name__ == "__main__": 
    run() 
import argparse 
import os 
import re
import shutil
from typing import Any   
from dotenv import load_dotenv
import google.generativeai as genai
from google.ai.generativelanguage import Content, Part

class Engineer: 
    begin: str 
    outro: str 
    root_dir: str 
    base_dir: str 
    prompts: list[str]
    model: genai.GenerativeModel
    proj_name: str 

    def __init__(self, begin: str, outro: str, args: list[str]) -> None:
        prompt_path, env_path, proj_path = args 
        api_key = load_api_key(env_path)
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name='gemini-pro')
        prompts = read_prompts(prompt_path)        
        root_dir = os.getcwd() 
        base_dir = os.path.join(root_dir, proj_path)
        os.makedirs(base_dir, exist_ok=True)
        os.chdir(base_dir)

        self.begin = begin     
        self.outro = outro
        self.root_dir = root_dir
        self.base_dir = base_dir
        self.prompts = prompts 
        self.model = model
        self.proj_name = proj_path
        
    def generate_response(self, input: str) -> str: 
        for i in range(5): 
            response = self.model.generate_content(input)
            try: 
                respose_text = response.text 
            except ValueError:
                continue
            break 
        return respose_text
    
    def parse_response(self, response: str) -> dict: 
        regex = r"(\S+)\n\s*```(\w*)[^\n]*\n(.+?)```"
        matches = re.finditer(regex, response, re.DOTALL)
        block_map = {}
        ctr = 0 
        for match in matches: 
            file_name = match.group(1)
            file_name = self.sanitize_name(file_name, match.group(2), ctr + 1)
            block_map[file_name] = match.group(3)  
            ctr += 1
        return block_map
    
    def create_file_from_block(self, file_name: str, block: str): 
        code = block 
        
        idx = file_name.rfind('/') 
        if idx != -1: 
            dir_name = file_name[:idx]
            os.makedirs(dir_name, exist_ok=True)
        with open(file_name, "w") as f: 
            f.write(code)
        return 

    def create_proj(self, block_map: dict): 
        for k, v in block_map.items(): 
            self.create_file_from_block(k, v)

    def create_input(self) -> str: 
        prompts_text = ". ".join(self.prompts)
        return self.begin + prompts_text + self.outro
    
    def sanitize_name(self, name: str, lang: str, ctr: int): 
        regex = r"\**(\S+?\.\w+)"
        matches = re.finditer(regex, name, re.DOTALL)
        for match in matches: 
            return match.group(1)
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
        return file_name 

def parse_arguements() -> list: 
    """Parses the command line arguements returning a list of arguements.
    Aborts the application if an arguement is missing"""
    
    parser = argparse.ArgumentParser(description="Configuration for the Prompts")
    parser.add_argument('--prompt', nargs=1, type=str, help="Location of the prompts file")
    parser.add_argument('--env', nargs=1, type=str, help="Location of .env file")
    parser.add_argument('--app_name', nargs=1, type=str, help="Name of the application")
    args = parser.parse_args()
    flag_values = [] 
    for flag, arg in args._get_kwargs(): 
        if arg == None: 
            print(f"{flag} is not set")
            exit(1)
        flag_values.append(arg[0])
    return flag_values 

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

def compress_folder(zip_dir: str): 
    root_dir = os.getcwd() 
    base_name = os.path.join(root_dir, zip_dir)
    shutil.make_archive(base_name, 'zip', root_dir, zip_dir)

def run(): 
    args = parse_arguements() 
    begin = '''You will be asked to generate code for an application, your reply should include the necessary code blocks and the names of the files at the top: 
           Your reply should be structured as follows: 
           Name of the file: <name-of-the-file>.extension
           {Code Block}. 
        '''
    eng = Engineer(begin,". Mention only the code blocks and the name of the file at the top of the code block", args)
    prompt = eng.create_input() 
    response = eng.generate_response(prompt)
    block_map = eng.parse_response(response=response)
    eng.create_proj(block_map=block_map)
    os.chdir(eng.root_dir)
    compress_folder(eng.proj_name)
    try: 
        shutil.rmtree(eng.base_dir)
    except OSError as e: 
        print("Error: %s - %s." % (e.filename, e.strerror)) 
        
if __name__ == "__main__": 
    run() 


# api_key = load_api_key(env_path)
# os.makedirs('app/', exist_ok=True)

# prompts = read_prompts(prompt_path)
# genai.configure(api_key=api_key)
# model = genai.GenerativeModel('gemini-pro')
# inp = ". ".join(prompts)
# for i in range(5): 
#     response = model.generate_content(begin + inp+". Mention only the code blocks and the name of the file at the top of the code block")
#     try: 
#         block_map = parse_response(response=response.text)
#     except ValueError: 
#         continue 
#     break 
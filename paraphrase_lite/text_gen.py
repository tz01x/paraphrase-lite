import dataclasses
import requests
import time
from typing import Generator

from hugchat import hugchat
from hugchat.login import Login

from .config import BASE_DIR

@dataclasses.dataclass
class TextGenInput:
    '''Text generator input'''
    tone: str
    text: str


class TextGenerator:

    def generate(self, input: TextGenInput) -> Generator:
        ...


class HuggingFaceTextGenerator(TextGenerator):
    __cookies = None
    __cookie_path_dir = (BASE_DIR/"cookies").as_posix()
    __system_prompts = 'you are the top class text suggestion ai,\
        you job is to MODIFY THE INPUT TEXT TO THE DESIRE OUTPUT TEXT;\
        and you will only return the output and nothing else and \
        Ensure proper grammar and spelling throughout the message.\
        You will not answers any type question ONLY MODIFY THE TEXT '
    @classmethod
    def login(cls, email, password):
        if not HuggingFaceTextGenerator.__cookies:
            sign = Login(email, password)
            cls.__cookies = sign.login(cookie_dir_path=cls.__cookie_path_dir, save_cookies=True)

        
    def __init__(self) -> None:
        if self.__cookies is None:
            raise Exception('Not Login')

        self.chatbot = hugchat.ChatBot(
            cookies=self.__cookies.get_dict(),
            system_prompt=self.__system_prompts
        )

    def generate(self, input: TextGenInput):
        try:
            for r in self.chatbot.query(self.__input_template(input), stream=True):
                if r:
                    yield r.get('token')
        except Exception as e:
            yield str(e)

    def __input_template(self, input: TextGenInput):
        return f'''
    Maintain a {input.tone} tone; and only return modified text
    input text: 
    {input.text}
    '''


class ApiTextGenerator(TextGenerator):
    base_url = "http://localhost:8000/streaming-view/"

    def generate(self, input: TextGenInput) -> Generator:
        url = f'{self.base_url}'
        s = requests.Session()
        with s.post(url, data=dataclasses.asdict(input), headers=None, stream=True, timeout=500) as resp:

            if resp.status_code == 200:
                for line in resp.iter_content(10):
                    if line:
                        yield line.decode('utf-8')
            else:
                yield 'Something want Wrong'


class MockTextGenerator(TextGenerator):
    def generate(self, input: TextGenInput) -> Generator:
        for text in input.text.strip().split(" "):
            time.sleep(0.05)
            yield text+" "

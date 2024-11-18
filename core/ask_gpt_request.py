import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import json
from typing import Dict, List
from core.config_utils import load_key
# import timeout_decorator
import boto3

api_set = load_key("api")
timeout = api_set.get("timeout", 60)

class AskGPTRequest:
    @staticmethod
    def get_gpt(args:dict):
        model = args["model"]
        if model.startswith("claude"):
            return Claude(args)
        

    def __init__(self, args):
        self.env = args.get("env", "local")
        self.max_sleep_time = args.get("max_sleep_time", 1)
        self.system_message = args.get("system_message", None)
        # self.logger.info(f"ENV:{self.env}")
        # self.logger.info(f"Set max_sleep_time:{self.max_sleep_time}")
        

    # @timeout_decorator.timeout(timeout)        
    def ask_gpt(self, messages:List[Dict]):
        return self.call_model(messages)

    def call_model(self, messages:List[Dict]):
        NotImplemented

    def get_region(self):
        NotImplemented


class Claude(AskGPTRequest):
    MODEL_DICT = {
        "claude3-haiku": 'anthropic.claude-3-haiku-20240307-v1:0',
        "claude3-sonnet": 'anthropic.claude-3-sonnet-20240229-v1:0',
        "claude3-opus": 'anthropic.claude-3-opus-20240229-v1:0',
        "claude3-5-sonnet-v2": "anthropic.claude-3-5-sonnet-20241022-v2:0",
    }

    def __init__(self, args):

        super().__init__(args)

        self.model = args.get("model", "claude3-haiku")
        self.model_id_anthropic = self.MODEL_DICT.get(self.model, None)     
        if self.model_id_anthropic is None:
            raise ValueError(f"Model {self.model} not found in MODEL_DICT")
                   
        # self.logger.info(f"set model_id_anthropic:{self.model_id_anthropic}")

        self.STREAM_ENABLED = args.get("claude_STREAM_ENABLED", False)
        self.ANTHROPIC_VERSION = args.get("claude_ANTHROPIC_VERSION", 'bedrock-2023-05-31')
        self.maximum_context_length = args.get("maximum_context_length", 4096)
        
        self.bedrock = boto3.client('bedrock-runtime')

    def call_model(self, messages: List[Dict]):
        message_dict = {
            "anthropic_version": self.ANTHROPIC_VERSION,
            "max_tokens": self.maximum_context_length,
            "messages": messages,
            "stop_sequences": ["\nHuman:"],
            "top_p": 0.1,
            "top_k": 10,
            "temperature": 0.0,
        }

        if self.system_message is not None:
            message_dict["system"] = self.system_message

        body = json.dumps(message_dict)

        if self.STREAM_ENABLED:
            ret_dict = self.streaming_text_generate(body)
        else:
            ret_dict = self.text_generate(body)

        ret_dict['region_name'] = self.get_region()

        return ret_dict
    
    def get_region(self):
        return self.bedrock.meta.region_name


    def text_generate(self, body):

        response = self.bedrock.invoke_model(
            body=body,
            modelId=self.model_id_anthropic,
            accept='application/json',
            contentType='application/json',
            
        )
        response_body = json.loads(response.get('body').read())

        content = response_body['content'][0]
        ret = content["text"]

        return {
            "ret": ret,
            "route": f"claude:{self.model}"
        }

    def streaming_text_generate(self, body):
        response = self.bedrock.invoke_model_with_response_stream(
            body=body,
            modelId=self.model_id_anthropic,
            accept='application/json',
            contentType='application/json',
        )

        ret = ""
        stream = response['body']
        if stream:
            for event in stream:
                chunk = event.get('chunk')
                if chunk:
                    chunk_obj = json.loads(chunk.get("bytes").decode())
                    if chunk_obj['type'] == 'content_block_delta':
                        # print(chunk_obj['delta']['text'], end='')
                        ret += chunk_obj['delta']['text']

        return {
            "ret": ret,
            "route": f"claude-stream:{self.model}"
        }


if __name__ == '__main__':

    print(f"api_set: {api_set}")

    prompt = '''Generate a random json output of 3 people with 3 keys: name, gender, address.'''
    messages = [{"role": "user", "content": prompt}]
    
    # base_url = api_set["base_url"].strip('/') + '/v1' if 'v1' not in api_set["base_url"] else api_set["base_url"]
    # client = OpenAI(api_key=api_set["key"], base_url=base_url)
    # response_format = {"type": "json_object"} if response_json and api_set["model"] in llm_support_json else None

    gpt = AskGPTRequest.get_gpt(api_set)

    response = gpt.ask_gpt(
        #model=api_set["model"],
        messages=messages,
        #response_format=response_format,
        #timeout=150 #! set timeout
    )

    response_data = response['ret']

    print(response_data)
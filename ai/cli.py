import yaml
import openai
import typer

app = typer.Typer()


def setup():

    with open('secrets.yaml') as f:
        secrets = yaml.safe_load(f)

    openai.organization = secrets["organization"]
    openai.api_key = secrets["api_key"]


setup()



def openai_chat(messages):
    return completion


def mock_openai_chat(message):
    return {
        "choices": [
            {
                "finish_reason": "stop",
                "index": 0,
                "message": {
                    "content": "\n\nAhoy, me hearties! Listen up for I come bearing news of the ChatGPT API. This be a fine treasure trove of an API, mark me words.\n\nYe see, ChatGPT be just the thing for all ye scallywags looking to add some piratey charm to yer chatbots and AI agents. With this API, ye can create chatbots that sound like a true-blue pirate - yarr!\n\nAnd there be more, me buckos! With ChatGPT, ye can train yer AI agents to speak like pirates, so they can help ye navigate the high seas and track down the booty. Ye can even use it to translate regular speech into pirate lingo, so ye can talk like a swashbuckler all day long.\n\nSo, if ye be looking for a fine addition to yer AI arsenal, look no further than ChatGPT. It's the treasure ye be seeking, mateys!",
                    "role": "assistant"
                }
            }
        ],
        "created": 1677815428,
        "id": "chatcmpl-6pqj6Oxrv69DRIQr2ywpsMghrPDqg",
        "model": "gpt-3.5-turbo-0301",
        "object": "chat.completion",
        "usage": {
            "completion_tokens": 193,
            "prompt_tokens": 23,
            "total_tokens": 216
        }
    }


chat_api = mock_openai_chat


@app.command()
def chat(message):

    prompt = True
    while prompt:
        prompt = input(">> ")
        res = chat_api(message)
        print(res["choices"][0]['message']['content'])


if __name__ == '__main__':
    pass

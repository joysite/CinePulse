from openai import OpenAI
import json
import re

class WriterAgent:
    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

    def generate_storyboard(self, story_prompt):
        """将故事主旨拆解为分镜脚本"""
        response = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a professional film director. Output a JSON with a 'scenes' list. Each scene has 'narration' and 'visual_desc'."},
                {"role": "user", "content": story_prompt}
            ],
            response_format={'type': 'json_object'}
        )
        content = response.choices[0].message.content
        return json.loads(re.sub(r'```json\s*|```', '', content).strip())

    def analyze_semantics(self, text):
        """语义联动分析：返回审美色彩与情绪"""
        response = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "Analyze text art style. Return JSON: {color_hex, mood, lighting}"},
                {"role": "user", "content": text}
            ],
            response_format={'type': 'json_object'}
        )
        return json.loads(response.choices[0].message.content)

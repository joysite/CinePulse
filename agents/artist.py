import requests
import os

class ArtistAgent:
    def __init__(self, api_key, style_bias):
        self.api_key = api_key
        self.style_bias = style_bias

    def generate_image(self, visual_desc, save_path):
        """审美纠偏型生图"""
        full_prompt = f"{self.style_bias}, {visual_desc}"
        url = "https://open.bigmodel.cn/api/paas/v4/images/generations"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {"model": "cogview-3-plus", "prompt": full_prompt}
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            resp = response.json()
            
            # 检查API响应状态
            if response.status_code != 200:
                print(f"Artist API Error: HTTP {response.status_code}, Response: {resp}")
                return None
            
            # 检查响应结构
            if 'data' not in resp:
                print(f"Artist API Error: Missing 'data' field. Response: {resp}")
                return None
            
            if not resp['data'] or len(resp['data']) == 0:
                print(f"Artist API Error: Empty data array. Response: {resp}")
                return None
            
            if 'url' not in resp['data'][0]:
                print(f"Artist API Error: Missing 'url' in data[0]. Response: {resp}")
                return None
            
            img_url = resp['data'][0]['url']
            img_data = requests.get(img_url, timeout=30).content
            
            if not img_data:
                print(f"Artist Error: Failed to download image from {img_url}")
                return None
                
            with open(save_path, "wb") as f:
                f.write(img_data)
            return save_path
            
        except requests.exceptions.RequestException as e:
            print(f"Artist Network Error: {e}")
            return None
        except KeyError as e:
            print(f"Artist Response Error: Missing key {e}")
            return None
        except Exception as e:
            print(f"Artist Error: {e}")
            return None
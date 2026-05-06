import requests
import os
import logging
import re

logger = logging.getLogger("CinePulse-Core")

class ArtistAgent:
    def __init__(self, api_key, style_bias):
        self.api_key = api_key
        # 预处理风格引导词：移除可能的特殊转义符
        self.style_bias = style_bias.strip().rstrip(',') + ", " 
        self.url = "https://open.bigmodel.cn/api/paas/v4/images/generations"

    def generate_image(self, visual_desc, save_path):
        # 1. 物理清洗：只保留中文、英文、数字、逗号、句号和空格
        clean_desc = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9,\.\s]', '', visual_desc)
        
        # 2. 拼接与长度硬限制
        # CogView-3-Plus 建议 Prompt 在 500 汉字或 1000 字符以内
        full_prompt = f"{self.style_bias}{clean_desc}"
        if len(full_prompt) > 800:
            full_prompt = full_prompt[:800]

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "cogview-3-plus", 
            "prompt": full_prompt,
            "size": "1024x1024"
        }
        
        try:
            # 记录发送出去的真实 Payload 长度
            logger.info(f"🎨 正在生图 | 模型: cogview-3-plus | 长度: {len(full_prompt)}")
            response = requests.post(self.url, headers=headers, json=payload, timeout=60)
            
            # 3.如果 400，捕获 API 返回的错误 JSON 详情
            if response.status_code != 200:
                error_body = response.json() if response.text else "Empty Response"
                logger.error(f"❌ Artist API 400 错误详情: {error_body}")
                
                # 如果是敏感词拦截，尝试使用极其简单的默认 Prompt 保底，确保程序不崩溃
                if "sensitive" in str(error_body).lower():
                    logger.warning("⚠️ 检测到敏感词拦截，启动安全 Prompt 保底策略...")
                    payload["prompt"] = f"{self.style_bias} cinematic movie scene, high quality"
                    response = requests.post(self.url, headers=headers, json=payload, timeout=60)
                
                if response.status_code != 200:
                    return None
                
            resp = response.json()
            img_url = resp['data'][0]['url']
            
            img_response = requests.get(img_url, timeout=30)
            if img_response.status_code == 200:
                with open(save_path, "wb") as f:
                    f.write(img_response.content)
                logger.info(f"✅ 图像生成成功: {save_path}")
                return save_path
            
            return None
                
        except Exception as e:
            logger.error(f"❌ ArtistAgent 异常: {str(e)}")
            return None

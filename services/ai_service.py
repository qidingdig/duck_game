#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI服务 - 接入ollama deepseekr1:8b模型
"""

import requests
import json
import time

class AIService:
    """AI对话服务"""
    
    def __init__(self, ollama_url="http://localhost:11434", model="deepseekr1:8b"):
        self.ollama_url = ollama_url
        self.model = model
        self.conversation_history = []
        
        # 测试连接
        self.test_connection()
    
    def test_connection(self):
        """测试ollama连接"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                print("AI服务连接成功！")
                return True
            else:
                print(f"AI服务连接失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"AI服务连接错误: {e}")
            print("请确保ollama服务正在运行: ollama serve")
            return False
    
    def chat(self, user_input):
        """与AI对话"""
        try:
            # 构建请求数据
            data = {
                "model": self.model,
                "prompt": user_input,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_tokens": 500
                }
            }
            
            # 发送请求
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result.get("response", "抱歉，我无法回答这个问题。")
                
                # 保存对话历史
                self.conversation_history.append({
                    "user": user_input,
                    "ai": ai_response,
                    "timestamp": time.time()
                })
                
                return ai_response
            else:
                return f"AI服务错误: {response.status_code}"
                
        except requests.exceptions.Timeout:
            return "AI服务响应超时，请稍后再试。"
        except requests.exceptions.ConnectionError:
            return "无法连接到AI服务，请检查ollama是否正在运行。"
        except Exception as e:
            return f"AI服务错误: {str(e)}"
    
    def get_conversation_history(self):
        """获取对话历史"""
        return self.conversation_history.copy()
    
    def clear_history(self):
        """清空对话历史"""
        self.conversation_history.clear()
    
    def get_model_info(self):
        """获取模型信息"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                for model in models:
                    if model.get("name") == self.model:
                        return model
            return None
        except Exception as e:
            print(f"获取模型信息失败: {e}")
            return None

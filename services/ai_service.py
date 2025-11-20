#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI服务 - 支持Ollama和OpenAI兼容API的统一接口
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    requests = None

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    OpenAI = None


class AIService:
    """
    AI对话服务 - 统一接口，支持多种后端
    
    支持两种调用方式：
    1. OpenAI兼容API（通过Ollama的/v1端点）
    2. Ollama原生API（/api/generate端点）
    """

    def __init__(
        self,
        backend: str = "openai",
        ollama_url: str = "http://localhost:11434",
        model: str = "deepseek-r1:8b",
        system_prompt: Optional[str] = None,
    ):
        """
        初始化AI服务。

        Args:
            backend: 后端类型，"openai" 或 "ollama"
            ollama_url: Ollama服务地址
            model: 模型名称
            system_prompt: 系统提示词（用于OpenAI格式）
        """
        self.backend = backend
        self.ollama_url = ollama_url
        self.model = model
        self.system_prompt = system_prompt or "你是唐老鸭，一个友善的卡通角色。请用中文回答用户的问题，保持幽默和友好的语调。"
        self.conversation_history: List[Dict[str, Any]] = []
        
        # 初始化OpenAI客户端（如果使用OpenAI兼容API）
        self._openai_client: Optional[Any] = None
        if backend == "openai" and HAS_OPENAI:
            try:
                self._openai_client = OpenAI(
                    api_key="ollama",
                    base_url=f"{ollama_url}/v1"
                )
            except Exception as e:
                print(f"初始化OpenAI客户端失败: {e}")
                self._openai_client = None
        
        # 测试连接
        self._connection_ok = self.test_connection()
    
    def test_connection(self) -> bool:
        """
        测试AI服务连接。

        Returns:
            True if connection successful, False otherwise
        """
        if not HAS_REQUESTS:
            print("警告: requests库未安装，无法使用AI服务")
            return False
        
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                print("✓ AI服务连接成功")
                return True
            else:
                print(f"✗ AI服务连接失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ AI服务连接错误: {e}")
            print("提示: 请确保ollama服务正在运行: ollama serve")
            return False
    
    def chat_completions(
        self,
        user_input: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500,
        timeout: int = 30,
    ) -> str:
        """
        使用OpenAI兼容API格式进行对话（推荐）。

        Args:
            user_input: 用户输入
            system_prompt: 系统提示词，如果为None则使用默认
            temperature: 温度参数（0-1）
            max_tokens: 最大token数
            timeout: 超时时间（秒）

        Returns:
            AI响应文本
        """
        if not self._connection_ok:
            return "抱歉，AI服务未连接，请检查Ollama服务是否正在运行。"
        
        system_prompt = system_prompt or self.system_prompt
        
        # 优先使用OpenAI兼容API
        if self.backend == "openai" and self._openai_client:
            try:
                response = self._openai_client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_input}
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=timeout
                )
                
                ai_response = response.choices[0].message.content
                if not ai_response or not ai_response.strip():
                    ai_response = "抱歉，我没有理解你的问题，请重新提问。"
                
                # 保存对话历史
                self._add_to_history(user_input, ai_response)
                
                return ai_response
                
            except Exception as e:
                print(f"OpenAI API调用错误: {e}")
                # 降级到Ollama原生API
                return self._chat_ollama_native(user_input, temperature, max_tokens, timeout)
        
        # 使用Ollama原生API
        return self._chat_ollama_native(user_input, temperature, max_tokens, timeout)
    
    def _chat_ollama_native(
        self,
        user_input: str,
        temperature: float = 0.7,
        max_tokens: int = 500,
        timeout: int = 30,
    ) -> str:
        """
        使用Ollama原生API进行对话（降级方案）。

        Args:
            user_input: 用户输入
            temperature: 温度参数
            max_tokens: 最大token数
            timeout: 超时时间

        Returns:
            AI响应文本
        """
        if not HAS_REQUESTS:
            return "抱歉，requests库未安装，无法使用AI服务。"
        
        try:
            # 构建请求数据
            data = {
                "model": self.model,
                "prompt": user_input,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            }
            
            # 发送请求
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=data,
                timeout=timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result.get("response", "抱歉，我无法回答这个问题。")
                
                # 保存对话历史
                self._add_to_history(user_input, ai_response)
                
                return ai_response
            else:
                return f"AI服务错误: HTTP {response.status_code}"
                
        except requests.exceptions.Timeout:
            return "AI服务响应超时，请稍后再试。"
        except requests.exceptions.ConnectionError:
            return "无法连接到AI服务，请检查ollama是否正在运行。"
        except Exception as e:
            return f"AI服务错误: {str(e)}"
    
    def chat(self, user_input: str) -> str:
        """
        与AI对话（兼容旧接口，使用默认参数）。

        Args:
            user_input: 用户输入

        Returns:
            AI响应文本
        """
        return self.chat_completions(user_input)
    
    def _add_to_history(self, user_input: str, ai_response: str) -> None:
        """添加对话到历史记录。"""
        self.conversation_history.append({
            "user": user_input,
            "ai": ai_response,
            "timestamp": time.time()
        })
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """
        获取对话历史。

        Returns:
            对话历史列表的副本
        """
        return self.conversation_history.copy()
    
    def clear_history(self) -> None:
        """清空对话历史。"""
        self.conversation_history.clear()
    
    def get_model_info(self) -> Optional[Dict[str, Any]]:
        """
        获取模型信息。

        Returns:
            模型信息字典，如果获取失败则返回None
        """
        if not HAS_REQUESTS:
            return None
        
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
    
    def is_available(self) -> bool:
        """
        检查AI服务是否可用。

        Returns:
            True if service is available, False otherwise
        """
        return self._connection_ok

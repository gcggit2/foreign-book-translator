"""LLMクライアントのラッパー

Phase 1ではGeminiのみ。Phase 2でOpenAI/Claudeも追加する想定の抽象化。
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from typing import Optional

from google import genai
from google.genai import types


@dataclass
class LLMResponse:
    """LLM応答を統一形式で返す"""
    text: str
    input_tokens: int = 0
    output_tokens: int = 0


class GeminiClient:
    """Gemini API クライアント（google-genai SDK使用）"""

    # モデル別の責務
    DETECTION_MODEL = "gemini-2.5-pro"   # 章検出は高品質モデル
    TRANSLATION_MODEL = "gemini-2.5-flash"  # 翻訳はコスト最適

    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("Gemini APIキーが指定されていません")
        self.client = genai.Client(api_key=api_key)

    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        response_json: bool = False,
        max_tokens: int = 32768,
        temperature: float = 0.3,
        retries: int = 10,
    ) -> LLMResponse:
        """汎用テキスト生成。

        Args:
            prompt: プロンプト本文
            model: モデル名（未指定なら TRANSLATION_MODEL）
            response_json: TrueならJSON形式での応答を要求
            max_tokens: 最大出力トークン数
            temperature: 0-1。低いほど決定的
            retries: 429/5xx時のリトライ回数
        """
        model = model or self.TRANSLATION_MODEL

        config_args = {
            "max_output_tokens": max_tokens,
            "temperature": temperature,
        }
        if response_json:
            config_args["response_mime_type"] = "application/json"
        config = types.GenerateContentConfig(**config_args)

        last_err = None
        for attempt in range(retries):
            try:
                resp = self.client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=config,
                )
                text = resp.text or ""
                usage = getattr(resp, "usage_metadata", None)
                in_tok = getattr(usage, "prompt_token_count", 0) if usage else 0
                out_tok = getattr(usage, "candidates_token_count", 0) if usage else 0
                return LLMResponse(text=text, input_tokens=in_tok, output_tokens=out_tok)
            except Exception as e:
                last_err = e
                err_str = str(e)
                msg = err_str.lower()
                # レート制限 (429): Geminiが指示するretryDelayを尊重
                if "429" in msg or "rate" in msg or "resource_exhausted" in msg or "quota" in msg:
                    wait = _parse_retry_delay(err_str) or min(30 * (attempt + 1), 90)
                    time.sleep(wait + 1)  # 少し余裕を持たせる
                    continue
                # サーバー一時障害 (5xx) - 500, 502, 503, 504 すべて対象
                if any(code in err_str for code in ["500", "502", "503", "504", "Bad Gateway", "Service Unavailable"]):
                    wait = min(2 ** attempt * 3, 60)
                    time.sleep(wait)
                    continue
                # それ以外は即時失敗
                raise

        raise RuntimeError(f"Gemini API失敗（{retries}回リトライ後）: {last_err}")

    def generate_json(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: int = 32768,
        temperature: float = 0.3,
    ) -> dict:
        """JSON形式での応答を取得してdictで返す"""
        resp = self.generate(
            prompt=prompt,
            model=model,
            response_json=True,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        try:
            return json.loads(resp.text)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Gemini応答がJSONとして解析できません: {resp.text[:500]}") from e


def make_client(provider: str, api_key: str):
    """プロバイダー名からクライアントを生成（Phase 2で拡張用）"""
    provider = provider.lower()
    if provider == "gemini":
        return GeminiClient(api_key)
    # Phase 2 で OpenAI, Claude を追加予定
    raise NotImplementedError(f"プロバイダー '{provider}' は未対応です")


def _parse_retry_delay(err_msg: str) -> Optional[int]:
    """エラーメッセージから 'retryDelay': '23s' を抜き出して秒数を返す"""
    m = re.search(r"'retryDelay'\s*:\s*'(\d+)s'", err_msg)
    if m:
        return int(m.group(1))
    return None

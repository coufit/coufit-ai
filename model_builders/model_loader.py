"""
model_loader_qwen.py

Production-friendly model loader for Qwen 3B-Instruct models.

Features:
- Safe device/quantization handling (supports hf_device_map)
- Auto chat templating (Qwen apply_chat_template)
- Token-efficient decoding (decode only new tokens)
- Flexible input/output token limits
- Tunable generation params (top_p, temperature, repetition_penalty, etc.)
- Optional stop sequences, seed, multiple returns
- Robust cleanup and OOM fallback handling
- Thread-safe singleton accessor

Requirements:
    transformers>=4.40, torch>=2.1
    accelerate/bitsandbytes optional
"""

from __future__ import annotations

import gc
import logging
import os
import threading
from dataclasses import dataclass
from typing import Iterable, List, Optional, Tuple, Union

import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
)

logger = logging.getLogger(__name__)
if not logger.handlers:
    logger.addHandler(logging.NullHandler())

# -----------------------------
# Configuration dataclasses
# -----------------------------

@dataclass
class LoaderConfig:
    model_name: str = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-3B-Instruct")
    cache_dir: Optional[str] = os.getenv("HF_CACHE_DIR")
    local_files_only: bool = bool(int(os.getenv("HF_LOCAL_ONLY", "0")))
    prefer_bf16: bool = True
    load_in_4bit: bool = bool(int(os.getenv("LOAD_IN_4BIT", "0")))
    load_in_8bit: bool = bool(int(os.getenv("LOAD_IN_8BIT", "0")))
    device_map: Optional[str] = os.getenv("DEVICE_MAP")
    torch_num_threads: Optional[int] = int(os.getenv("TORCH_NUM_THREADS", "0")) or None


@dataclass
class GenerateConfig:
    max_input_tokens: int = 2048
    max_new_tokens: int = 512
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: Optional[int] = None
    repetition_penalty: float = 1.05
    typical_p: Optional[float] = 0.5
    no_repeat_ngram_size: int = 4
    ban_digits: bool = False
    do_sample: bool = True
    use_cache: bool = True
    seed: Optional[int] = None
    num_return_sequences: int = 1
    stop_sequences: Optional[List[str]] = None


# -----------------------------
# Loader
# -----------------------------

class QwenLoader:
    def __init__(self, cfg: Optional[LoaderConfig] = None):
        self.cfg = cfg or LoaderConfig()
        self.model: Optional[AutoModelForCausalLM] = None
        self.tokenizer: Optional[AutoTokenizer] = None
        self.device: str = "cuda" if torch.cuda.is_available() else "cpu"

        if self.cfg.torch_num_threads:
            try:
                torch.set_num_threads(self.cfg.torch_num_threads)
                logger.info("torch num threads set to %s", self.cfg.torch_num_threads)
            except Exception:
                logger.exception("Failed to set torch num threads")

        self._load()

    def _select_dtype(self) -> torch.dtype:
        if self.device == "cuda":
            return torch.bfloat16 if self.cfg.prefer_bf16 and torch.cuda.is_bf16_supported() else torch.float16
        return torch.bfloat16 if self.cfg.prefer_bf16 and hasattr(torch, "bfloat16") else torch.float32

    def _load(self) -> None:
        """Load tokenizer and model with robust fallbacks."""
        logger.info("Loading tokenizer: %s", self.cfg.model_name)
        tok_kwargs = {
            "cache_dir": self.cfg.cache_dir,
            "local_files_only": self.cfg.local_files_only,
            "use_fast": True,
        }
        self.tokenizer = AutoTokenizer.from_pretrained(self.cfg.model_name, **tok_kwargs)

        # Ensure pad token exists
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        # Qwen models expect right padding
        self.tokenizer.padding_side = "right"

        dtype = self._select_dtype()
        model_kwargs = {
            "cache_dir": self.cfg.cache_dir,
            "local_files_only": self.cfg.local_files_only,
            "torch_dtype": dtype,
        }

        if self.cfg.load_in_4bit:
            model_kwargs.update({"load_in_4bit": True})
        elif self.cfg.load_in_8bit:
            model_kwargs.update({"load_in_8bit": True})

        if self.cfg.device_map:
            model_kwargs["device_map"] = self.cfg.device_map
        elif self.cfg.load_in_4bit or self.cfg.load_in_8bit:
            model_kwargs["device_map"] = "auto"

        tried_variants: List[Tuple[str, dict]] = []

        def _attempt(kwargs: dict) -> AutoModelForCausalLM:
            logger.info("Loading model: %s kwargs=%s", self.cfg.model_name,
                        {k: kwargs.get(k) for k in ("torch_dtype", "load_in_4bit", "load_in_8bit", "device_map")})
            model = AutoModelForCausalLM.from_pretrained(self.cfg.model_name, **kwargs)
            if not kwargs.get("device_map"):
                try:
                    model.to(self.device)
                except Exception:
                    logger.exception("Failed to move model to %s; staying on CPU", self.device)
            model.eval()
            return model

        variants: List[dict] = [model_kwargs]
        if self.device == "cuda":
            v_fp16 = dict(model_kwargs)
            v_fp16["torch_dtype"] = torch.float16
            if v_fp16 not in variants:
                variants.append(v_fp16)
        else:
            v_fp32 = dict(model_kwargs)
            v_fp32["torch_dtype"] = torch.float32
            if v_fp32 not in variants:
                variants.append(v_fp32)

        last_err: Optional[Exception] = None
        for var in variants:
            try:
                self.model = _attempt(var)
                break
            except RuntimeError as e:
                last_err = e
                tried_variants.append(("RuntimeError", var))
                logger.exception("Model load failed with RuntimeError; trying next variant")
                self._collect_garbage()
            except Exception as e:
                last_err = e
                tried_variants.append((type(e).__name__, var))
                logger.exception("Model load failed; trying next variant")
                self._collect_garbage()
        if self.model is None:
            raise RuntimeError(f"Failed to load model after variants: {tried_variants}") from last_err
        logger.info("Model loaded successfully")

    # -----------------------------
    # Generation
    # -----------------------------

    @torch.inference_mode()
    def generate_text(
        self,
        prompt: Union[str, List[dict]],
        gen_cfg: Optional[GenerateConfig] = None,
        **overrides,
    ) -> Union[str, List[str]]:
        """Generate text from a prompt or chat messages.

        - If `prompt` is a list of {"role": ..., "content": ...}, it uses Qwen chat template.
        - If `prompt` is str, it wraps as a single user message.
        """
        if self.model is None or self.tokenizer is None:
            raise RuntimeError("Model not loaded")

        cfg = gen_cfg or GenerateConfig()
        for k, v in overrides.items():
            if hasattr(cfg, k):
                setattr(cfg, k, v)

        if cfg.seed is not None:
            torch.manual_seed(cfg.seed)

        # Build prompt (use chat template if needed)
        if isinstance(prompt, str):
            messages = [{"role": "user", "content": prompt}]
        else:
            messages = prompt

        prompt_text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )

        enc = self.tokenizer(
            prompt_text,
            return_tensors="pt",
            truncation=True,
            max_length=cfg.max_input_tokens,
            padding=False,
        )

        has_device_map = getattr(self.model, "hf_device_map", None) is not None
        if not has_device_map:
            enc = {k: v.to(self.device) for k, v in enc.items()}

        gen_kwargs = dict(
            max_new_tokens=cfg.max_new_tokens,
            temperature=cfg.temperature,
            top_p=cfg.top_p,
            do_sample=cfg.do_sample,
            repetition_penalty=cfg.repetition_penalty,
            use_cache=cfg.use_cache,
            num_return_sequences=cfg.num_return_sequences,
            eos_token_id=self.tokenizer.eos_token_id,
            pad_token_id=self.tokenizer.pad_token_id,
        )
        if cfg.top_k is not None:
            gen_kwargs["top_k"] = cfg.top_k

        enc = {k: v for k, v in enc.items() if k in ("input_ids", "attention_mask", "position_ids")}
        outputs = self.model.generate(**enc, **gen_kwargs)

        if outputs.dim() == 1:
            outputs = outputs.unsqueeze(0)

        prompt_len = enc["input_ids"].shape[1]
        decoded: List[str] = []
        for i in range(outputs.size(0)):
            gen_ids = outputs[i]
            new_ids = gen_ids[prompt_len:]
            text = self.tokenizer.decode(new_ids, skip_special_tokens=True).strip()
            if cfg.stop_sequences:
                text = _apply_stops(text, cfg.stop_sequences)
            decoded.append(text)

        return decoded[0] if cfg.num_return_sequences == 1 else decoded

    # -----------------------------
    # Utilities
    # -----------------------------

    def _collect_garbage(self) -> None:
        try:
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                if hasattr(torch.cuda, "ipc_collect"):
                    torch.cuda.ipc_collect()
        except Exception:
            logger.exception("GC/empty_cache failed")

    def cleanup(self) -> None:
        logger.info("Cleaning up model/tokenizer")
        try:
            del self.model
            del self.tokenizer
        except Exception:
            pass
        self.model = None
        self.tokenizer = None
        self._collect_garbage()


# -----------------------------
# Singleton accessor
# -----------------------------

_singleton_lock = threading.Lock()
_singleton_instance: Optional[QwenLoader] = None


def get_loader(cfg: Optional[LoaderConfig] = None) -> QwenLoader:
    global _singleton_instance
    if _singleton_instance is None:
        with _singleton_lock:
            if _singleton_instance is None:
                _singleton_instance = QwenLoader(cfg)
    return _singleton_instance


# -----------------------------
# Helpers
# -----------------------------

def _apply_stops(text: str, stops: Iterable[str]) -> str:
    cut = len(text)
    for s in stops:
        if not s:
            continue
        pos = text.find(s)
        if pos != -1:
            cut = min(cut, pos)
    return text[:cut].rstrip()


# -----------------------------
# Example usage
# -----------------------------
if __name__ == "__main__":
    loader = get_loader()
    out = loader.generate_text(
        "Qwen 모델은 어떤 구조로 되어 있고, 파이토치 기반에서 어떻게 학습되나요? 자세히 설명해줘.",
        temperature=0.6,
        top_p=0.9,
        repetition_penalty=1.1,
        max_new_tokens=800,
    )
    print(out)

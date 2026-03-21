"""
中英混合 TTS (Text-to-Speech) 文字转语音引擎
基于 ONNX 模型实现，支持中英文无缝混合合成
支持长文本自动分块、并发处理
"""
import os
import re
import sys
import platform
import logging
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
import onnxruntime as ort
import soundfile as sf
import kaldi_native_fbank as knf
from pypinyin import pinyin, Style
from piper_phonemize import phonemize_espeak

from .config import settings


# 配置常量
MAX_TOKENS = 800  # 每块最大token数
MAX_CONCURRENT_CHUNKS = 2  # 最大并发数
CHUNK_PAUSE_DURATION = 0.2  # 分块间静音时长(秒)
FAILED_CHUNK_SILENCE_DURATION = 0.5  # 失败分块静音时长(秒)
SENTENCE_DELIMITERS = '。！？.!?！？'  # 句子分隔符
PAUSE_DELIMITERS = '，、；,;,'  # 次级分隔符

# 模型下载链接
MODEL_BASE_URL = "https://modelscope.cn/models/dengcunqin/matcha_tts_zh_en_20251010/resolve/master"
MODEL_FILES = {
    "model-steps-6.onnx": f"{MODEL_BASE_URL}/model-steps-6.onnx",
    "vocab_tts.txt": f"{MODEL_BASE_URL}/vocab_tts.txt",
    "vocos-16khz-univ.onnx": f"{MODEL_BASE_URL}/vocos-16khz-univ.onnx",
}

logger = logging.getLogger(__name__)


def download_file(url: str, dest: Path, description: str = "文件") -> None:
    """
    下载文件，支持 Windows 和 macOS 不同方式

    Args:
        url: 下载链接
        dest: 目标路径
        description: 文件描述（用于日志）
    """
    dest.parent.mkdir(parents=True, exist_ok=True)

    system = platform.system()
    logger.info(f"正在下载{description}: {url}")
    logger.info(f"目标路径: {dest}")
    logger.info(f"系统平台: {system}")

    try:
        # 设置请求头，模拟浏览器访问
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        request = urllib.request.Request(url, headers=headers)

        # 下载文件
        with urllib.request.urlopen(request, timeout=300) as response:
            total_size = response.getheader('Content-Length')
            if total_size:
                total_size = int(total_size)
                logger.info(f"文件大小: {total_size / 1024 / 1024:.2f} MB")

            with open(dest, 'wb') as f:
                downloaded = 0
                chunk_size = 8192
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)

                    # 显示进度
                    if total_size:
                        progress = downloaded / total_size * 100
                        if downloaded % (1024 * 1024) == 0:  # 每1MB输出一次
                            logger.info(f"下载进度: {progress:.1f}%")

        logger.info(f"下载完成: {dest}")

    except urllib.error.URLError as e:
        logger.error(f"下载失败: {e}")
        if dest.exists():
            dest.unlink()
        raise RuntimeError(f"下载{description}失败: {e}")


def ensure_model_files(model_dir: Path) -> None:
    """
    确保模型文件存在，不存在则下载

    Args:
        model_dir: 模型目录
    """
    model_dir.mkdir(parents=True, exist_ok=True)

    for filename, url in MODEL_FILES.items():
        file_path = model_dir / filename

        if file_path.exists():
            # 检查文件大小，确保下载完整
            size = file_path.stat().st_size
            if size > 1000:  # 至少1KB
                logger.info(f"模型文件已存在: {file_path}")
                continue
            else:
                logger.warning(f"模型文件不完整，重新下载: {file_path}")
                file_path.unlink()

        # 下载文件
        logger.info(f"开始下载模型文件: {filename}")
        try:
            download_file(url, file_path, filename)
        except Exception as e:
            logger.error(f"下载 {filename} 失败: {e}")
            raise


class OnnxAcousticModel:
    """声学模型 - token IDs -> Mel频谱"""

    def __init__(self, filename: str):
        session_opts = ort.SessionOptions()
        session_opts.inter_op_num_threads = 1
        session_opts.intra_op_num_threads = 2

        self.model = ort.InferenceSession(
            filename,
            sess_options=session_opts,
            providers=["CPUExecutionProvider"],
        )

        metadata = self.model.get_modelmeta().custom_metadata_map
        self.sample_rate = int(metadata.get("sample_rate", 16000))
        logger.info(f"声学模型加载成功: {filename}, 采样率: {self.sample_rate}Hz")

    def __call__(self, x: np.ndarray, noise_scale: float = 1.0, length_scale: float = 1.0) -> np.ndarray:
        """
        Args:
            x: (batch_size, seq_len) - token IDs
            noise_scale: 噪声比例
            length_scale: 长度比例（控制语速，1/speed）
        Returns:
            mel: (batch_size, feat_dim, num_frames)
        """
        assert x.ndim == 2 and x.shape[0] == 1

        x_lengths = np.array([x.shape[1]], dtype=np.int64)

        mel = self.model.run(
            [self.model.get_outputs()[0].name],
            {
                self.model.get_inputs()[0].name: x,
                self.model.get_inputs()[1].name: x_lengths,
                self.model.get_inputs()[2].name: np.array([noise_scale], dtype=np.float32),
                self.model.get_inputs()[3].name: np.array([length_scale], dtype=np.float32),
            },
        )[0]

        return mel


class OnnxVocosModel:
    """Vocos声码器 - Mel频谱 -> 音频"""

    def __init__(self, filename: str):
        session_opts = ort.SessionOptions()
        session_opts.inter_op_num_threads = 1
        session_opts.intra_op_num_threads = 1

        self.model = ort.InferenceSession(
            filename,
            sess_options=session_opts,
            providers=["CPUExecutionProvider"],
        )
        logger.info(f"Vocos声码器加载成功: {filename}")

    def __call__(self, x: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Args:
            x: (N, feat_dim, num_frames) - Mel频谱
        Returns:
            mag, x, y: 幅度谱和复数谱分量
        """
        assert x.ndim == 3 and x.shape[0] == 1

        mag, x, y = self.model.run(
            [
                self.model.get_outputs()[0].name,
                self.model.get_outputs()[1].name,
                self.model.get_outputs()[2].name,
            ],
            {self.model.get_inputs()[0].name: x},
        )

        return mag, x, y


class MixedTTSEngine:
    """中英混合 TTS 引擎"""

    def __init__(self, model_dir: str):
        """
        初始化 TTS 引擎

        Args:
            model_dir: 模型文件目录
        """
        self.model_dir = Path(model_dir)

        # 确保模型文件存在（不存在则下载）
        logger.info(f"检查模型文件目录: {self.model_dir}")
        ensure_model_files(self.model_dir)

        # 加载模型
        self.am = OnnxAcousticModel(str(self.model_dir / "model-steps-6.onnx"))
        self.vocoder = OnnxVocosModel(str(self.model_dir / "vocos-16khz-univ.onnx"))

        # 加载词汇表
        self.pinyin_to_id = self._load_vocab(str(self.model_dir / "vocab_tts.txt"))

        # ISTFT配置（复用）
        self.istft_config = knf.StftConfig(
            n_fft=1024,
            hop_length=256,
            win_length=1024,
            window_type="hann",
            center=True,
            pad_mode="reflect",
            normalized=False,
        )
        self.istft = knf.IStft(self.istft_config)

        logger.info("TTS引擎初始化完成")

    def _load_vocab(self, vocab_file: str) -> dict:
        """加载词汇表"""
        with open(vocab_file, 'r', encoding='utf-8') as f:
            vocab = [x.strip() for x in f.readlines()]
        pinyin_to_id = {p: idx + 1 for idx, p in enumerate(vocab)}
        logger.info(f"词汇表加载成功: {len(pinyin_to_id)}个条目")
        return pinyin_to_id

    # ========== 文本预处理 ==========

    def _preprocess_quote_mark(self, text: str) -> str:
        """替换各种引号为空格"""
        # 中文双引号
        text = text.replace('"', ' ').replace('"', ' ')
        text = text.replace('"', ' ').replace('"', ' ')
        # 英文引号
        text = text.replace("'", " ").replace("'", " ")
        # 其他引号
        text = text.replace('「', ' ').replace('」', ' ')
        text = text.replace('『', ' ').replace('』', ' ')
        text = text.replace('«', ' ').replace('»', ' ')
        return text

    def _preprocess_dash(self, text: str) -> str:
        """替换破折号为空格"""
        text = text.replace('—', ' ').replace('–', ' ')
        return text

    def _preprocess_mixed_text(self, text: str) -> str:
        """在中英文边界添加空格，改善发音"""
        chinese_pattern = r'[\u4e00-\u9fff]'
        alnum_pattern = r'[a-zA-Z0-9]'
        chinese_punct = r'[，。！？：；、]'

        # 中文 + 英文/数字 → 添加空格
        text = re.sub(
            rf'({chinese_pattern})(?![\s{chinese_punct}])({alnum_pattern})',
            r'\1 \2',
            text
        )

        # 英文/数字 + 中文 → 添加空格
        text = re.sub(
            rf'({alnum_pattern})(?!\s)({chinese_pattern})',
            r'\1 \2',
            text
        )

        # 清理多余空格
        text = re.sub(r' +', ' ', text)
        return text

    # ========== Token 估算与分块 ==========

    def _estimate_token_count(self, text: str) -> int:
        """估算文本的token数量"""
        chinese_count = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        english_words = len([w for w in text.split() if any(c.isalpha() for c in w)])
        punctuation = sum(1 for c in text if c in '。！？.!?！？，,、；;')

        # 保守估算
        return int(chinese_count * 1.5 + english_words * 4 + punctuation)

    def _split_text_into_chunks(self, text: str, max_tokens: int = MAX_TOKENS) -> List[str]:
        """智能分割长文本"""
        if self._estimate_token_count(text) <= max_tokens:
            return [text]

        chunks = []
        sentences = []
        current_sentence = ""

        # 按句子分隔符分割
        for char in text:
            current_sentence += char
            if char in SENTENCE_DELIMITERS:
                sentences.append(current_sentence)
                current_sentence = ""

        if current_sentence:
            sentences.append(current_sentence)

        # 组合成chunks
        current_chunk = ""
        for sentence in sentences:
            if self._estimate_token_count(sentence) > max_tokens:
                # 单句过长，按次级分隔符分割
                sub_parts = self._split_by_secondary_delimiters(sentence, max_tokens)
                chunks.extend(sub_parts)
                current_chunk = ""
                continue

            test_chunk = current_chunk + sentence
            if self._estimate_token_count(test_chunk) <= max_tokens:
                current_chunk = test_chunk
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def _split_by_secondary_delimiters(self, text: str, max_tokens: int) -> List[str]:
        """按次级分隔符分割过长句子"""
        parts = []
        current_part = ""

        for char in text:
            current_part += char

            if char in PAUSE_DELIMITERS:
                if self._estimate_token_count(current_part) >= max_tokens * 0.8:
                    parts.append(current_part.strip())
                    current_part = ""

            if self._estimate_token_count(current_part) >= max_tokens:
                parts.append(current_part.strip())
                current_part = ""

        if current_part:
            parts.append(current_part.strip())

        return parts

    # ========== 文本转Token ==========

    def _text_to_tokens(self, text: str) -> List[int]:
        """将文本转换为token ID列表"""
        # 预处理
        text = self._preprocess_quote_mark(text)
        text = self._preprocess_dash(text)
        text = self._preprocess_mixed_text(text)

        result = []
        i = 0

        while i < len(text):
            if '\u4e00' <= text[i] <= '\u9fff':  # 中文
                chinese_part = ""
                while i < len(text) and '\u4e00' <= text[i] <= '\u9fff':
                    chinese_part += text[i]
                    i += 1
                result.extend(self._chinese_to_pinyin_ids(chinese_part))

            elif text[i].isalpha():  # 英文
                english_part = ""
                while i < len(text) and text[i].isalpha():
                    english_part += text[i]
                    i += 1
                result.extend(self._english_to_phoneme_ids(english_part))

            else:  # 标点等
                char = text[i].replace('，', ',').replace('。', '.').replace('！', '!').replace('？', '?')
                result.append(self.pinyin_to_id.get(char, 1))
                i += 1

        return result

    def _chinese_to_pinyin_ids(self, text: str) -> List[int]:
        """中文转拼音ID"""
        result = pinyin(text, style=Style.TONE3, neutral_tone_with_five=True)
        pinyin_list = [item[0] for item in result]
        return [self.pinyin_to_id.get(p, 1) for p in pinyin_list]

    def _english_to_phoneme_ids(self, text: str) -> List[int]:
        """英文转音素ID"""
        ipa_list = phonemize_espeak(text, "en-us")
        if not ipa_list:
            return [1]

        ipa_str = ''.join(ipa_list[0])
        gruut_str = self._convert_ipa_to_gruut(ipa_str)
        return [self.pinyin_to_id.get(p, 1) for p in list(gruut_str)]

    def _convert_ipa_to_gruut(self, ipa_input: str) -> str:
        """IPA转gruut格式"""
        text = ipa_input if isinstance(ipa_input, str) else "".join(ipa_input)

        replacements = [
            ("ɝ", "ɜɹ"), ("ɚ", "əɹ"),
            ("eɪ", "A"), ("aɪ", "I"), ("ɔɪ", "Y"),
            ("oʊ", "O"), ("əʊ", "O"), ("aʊ", "W"),
            ("tʃ", "ʧ"), ("dʒ", "ʤ"),
            ("ː", ""), ("g", "ɡ"), ("r", "ɹ"), ("e", "ɛ"),
        ]

        for pattern, replacement in replacements:
            text = text.replace(pattern, replacement)

        return text

    # ========== 音频处理 ==========

    def _synthesize_single(self, text: str, speed: float = 1.0) -> Tuple[np.ndarray, int]:
        """合成单个文本片段"""
        token_ids = self._text_to_tokens(text)

        if not token_ids:
            raise ValueError("文本转换后无有效token")

        if len(token_ids) > 1000:
            raise ValueError(f"Token数量 ({len(token_ids)}) 超过模型限制 (1000)")

        length_scale = 1.0 / speed
        tokens = np.array([token_ids], dtype=np.int64)

        # 声学模型
        mel = self.am(tokens, noise_scale=1.0, length_scale=length_scale)

        # 声码器
        mag, x, y = self.vocoder(mel)

        # ISTFT
        stft_result = knf.StftResult(
            real=(mag * x)[0].transpose().reshape(-1).tolist(),
            imag=(mag * y)[0].transpose().reshape(-1).tolist(),
            num_frames=mag.shape[2],
        )
        audio = np.array(self.istft(stft_result), dtype=np.float32)

        return audio, self.am.sample_rate

    def _concatenate_audio(self, audio_segments: List[np.ndarray]) -> np.ndarray:
        """连接音频片段，添加间隙"""
        if not audio_segments:
            return np.array([])
        if len(audio_segments) == 1:
            return audio_segments[0]

        silence_duration = int(CHUNK_PAUSE_DURATION * self.am.sample_rate)
        silence = np.zeros(silence_duration, dtype=audio_segments[0].dtype)

        result = []
        for i, segment in enumerate(audio_segments):
            result.append(segment)
            if i < len(audio_segments) - 1:
                result.append(silence)

        return np.concatenate(result)

    def _synthesize_chunks_concurrent(self, chunks: List[str], speed: float) -> List[np.ndarray]:
        """并发处理多个文本块"""
        max_workers = min(len(chunks), MAX_CONCURRENT_CHUNKS)
        audio_segments = [None] * len(chunks)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_index = {}
            for i, chunk in enumerate(chunks):
                logger.info(f"提交分块 {i+1}/{len(chunks)}: {len(chunk)} 字符")
                future = executor.submit(self._synthesize_single, chunk, speed)
                future_to_index[future] = (i, chunk)

            for future in as_completed(future_to_index):
                i, chunk = future_to_index[future]
                try:
                    audio, _ = future.result()
                    audio_segments[i] = audio
                    logger.info(f"分块 {i+1} 合成成功: {len(audio)} samples")
                except Exception as e:
                    logger.error(f"分块 {i+1} 合成失败: {e}")
                    silence_samples = int(FAILED_CHUNK_SILENCE_DURATION * self.am.sample_rate)
                    audio_segments[i] = np.zeros(silence_samples, dtype=np.float32)

        return [seg for seg in audio_segments if seg is not None]

    # ========== 主接口 ==========

    def synthesize(
        self,
        text: str,
        output_path: str,
        noise_scale: float = 1.0,
        length_scale: float = 1.0,
    ) -> str:
        """
        合成语音

        Args:
            text: 要合成的文本（支持中英混合、长文本）
            output_path: 输出文件路径
            noise_scale: 噪声比例
            length_scale: 长度比例（越大越慢）
        """
        if not text or not text.strip():
            raise ValueError("文本不能为空")

        text = text.strip()
        speed = 1.0 / length_scale  # 转换：length_scale越大越慢

        estimated_tokens = self._estimate_token_count(text)
        logger.info(f"文本长度: {len(text)} 字符, 估算token数: {estimated_tokens}")

        if estimated_tokens <= MAX_TOKENS:
            # 短文本直接处理
            audio, sample_rate = self._synthesize_single(text, speed)
        else:
            # 长文本分块处理
            logger.info("文本较长，启用分块处理")
            chunks = self._split_text_into_chunks(text)
            logger.info(f"文本已分割为 {len(chunks)} 个分块")

            audio_segments = self._synthesize_chunks_concurrent(chunks, speed)
            audio = self._concatenate_audio(audio_segments)
            sample_rate = self.am.sample_rate

        # 保存
        sf.write(output_path, audio, sample_rate, "PCM_16")
        logger.info(f"音频已保存: {output_path}")

        return output_path

    async def synthesize_async(
        self,
        text: str,
        output_path: str,
        noise_scale: float = 1.0,
        length_scale: float = 1.0,
    ) -> str:
        """异步合成语音"""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.synthesize(text, output_path, noise_scale, length_scale)
        )


# 全局引擎实例
_mixed_engine: Optional[MixedTTSEngine] = None


def get_model_dir() -> Path:
    """
    获取模型目录路径

    优先级：
    1. 项目根目录下的 models/ 目录（开发环境）
    2. 用户目录下的 ~/.voicestudio/models/mixed_tts/
    """
    # 检查项目目录下是否有模型
    project_root = Path(__file__).parent.parent.parent
    project_models = project_root / "models"

    if (project_models / "model-steps-6.onnx").exists():
        logger.info(f"使用项目目录下的模型: {project_models}")
        return project_models

    # 使用用户目录
    model_dir = settings.models_dir / "mixed_tts"
    logger.info(f"使用用户目录存储模型: {model_dir}")
    return model_dir


def get_mixed_tts_engine() -> MixedTTSEngine:
    """获取中英混合 TTS 引擎实例"""
    global _mixed_engine
    if _mixed_engine is None:
        model_dir = get_model_dir()
        _mixed_engine = MixedTTSEngine(str(model_dir))

    return _mixed_engine
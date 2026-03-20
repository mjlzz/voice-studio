"""
中英混合 TTS (Text-to-Speech) 文字转语音引擎
基于 ONNX 模型实现，支持中英文无缝混合合成
"""
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass

import numpy as np
import onnxruntime as ort
import soundfile as sf

from .config import settings


@dataclass
class MixedTTSEngine:
    """中英混合 TTS 引擎 - 基于 ONNX 模型"""

    model_path: Path
    vocoder_path: Path
    vocab_path: Path

    def __post_init__(self):
        """初始化模型和词汇表"""
        self._am_model = None
        self._vocoder_model = None
        self._pinyin_to_id = None
        self._sample_rate = 16000

    def _load_vocab(self) -> dict:
        """加载词汇表"""
        if self._pinyin_to_id is None:
            with open(self.vocab_path, 'r', encoding='utf-8') as f:
                vocab = [x.strip() for x in f.readlines()]
            self._pinyin_to_id = {pinyin: idx + 1 for idx, pinyin in enumerate(vocab)}
        return self._pinyin_to_id

    def _load_am_model(self):
        """加载声学模型"""
        if self._am_model is None:
            session_opts = ort.SessionOptions()
            session_opts.inter_op_num_threads = 1
            session_opts.intra_op_num_threads = 2

            self._am_model = ort.InferenceSession(
                str(self.model_path),
                sess_options=session_opts,
                providers=["CPUExecutionProvider"],
            )

            # 获取采样率
            metadata = self._am_model.get_modelmeta().custom_metadata_map
            if "sample_rate" in metadata:
                self._sample_rate = int(metadata["sample_rate"])

    def _load_vocoder_model(self):
        """加载声码器模型"""
        if self._vocoder_model is None:
            session_opts = ort.SessionOptions()
            session_opts.inter_op_num_threads = 1
            session_opts.intra_op_num_threads = 1

            self._vocoder_model = ort.InferenceSession(
                str(self.vocoder_path),
                sess_options=session_opts,
                providers=["CPUExecutionProvider"],
            )

    def _text_to_pinyin_with_numbers(self, text: str) -> str:
        """
        将中文文本转换为拼音，音调用数字1-5表示
        1,2,3,4代表四声，5代表轻声
        """
        from pypinyin import pinyin, Style

        result = pinyin(text, style=Style.TONE3, neutral_tone_with_five=True)
        pinyin_list = [item[0] for item in result]

        return ' '.join(pinyin_list).replace('，', ',').replace('。', '.').replace('！', '!').replace('？', '?')

    def _convert_to_gruut_en_us_strict(self, ipa_input: str) -> str:
        """
        将标准 IPA 转换为 gruut en-us 内部格式
        """
        if isinstance(ipa_input, list):
            text = "".join(ipa_input)
        else:
            text = ipa_input

        replacements = [
            ("ɝ", "ɜɹ"),
            ("ɚ", "əɹ"),
            ("eɪ", "A"),
            ("aɪ", "I"),
            ("ɔɪ", "Y"),
            ("oʊ", "O"),
            ("əʊ", "O"),
            ("aʊ", "W"),
            ("tʃ", "ʧ"),
            ("dʒ", "ʤ"),
            ("ː", ""),
            ("g", "ɡ"),
            ("r", "ɹ"),
            ("e", "ɛ"),
        ]

        for pattern, replacement in replacements:
            text = text.replace(pattern, replacement)

        return text

    def _split_and_process(self, text: str, pinyin_to_id: dict) -> List[int]:
        """
        处理中英混合文本，转换为token ID列表
        """
        from piper_phonemize import phonemize_espeak

        result = []
        i = 0

        while i < len(text):
            if '\u4e00' <= text[i] <= '\u9fff':  # 中文字符
                chinese_part = ""
                while i < len(text) and '\u4e00' <= text[i] <= '\u9fff':
                    chinese_part += text[i]
                    i += 1
                # 中文转拼音ID
                pinyin_text = self._text_to_pinyin_with_numbers(chinese_part)
                result.extend([pinyin_to_id.get(p, 1) for p in pinyin_text.split(' ')])

            elif text[i].isalpha():  # 英文字符
                english_part = ""
                while i < len(text) and text[i].isalpha():
                    english_part += text[i]
                    i += 1
                # 英文转音素ID
                phonemes = phonemize_espeak(english_part, "en-us")
                if phonemes and phonemes[0]:
                    converted = self._convert_to_gruut_en_us_strict(''.join(phonemes[0]))
                    result.extend([pinyin_to_id.get(p, 1) for p in list(converted)])

            else:  # 标点符号等
                char = text[i].replace('，', ',').replace('。', '.').replace('！', '!').replace('？', '?')
                result.append(pinyin_to_id.get(char, 1))
                i += 1

        return result

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
            text: 要合成的文本（支持中英混合）
            output_path: 输出文件路径 (WAV格式)
            noise_scale: 噪声比例 (影响随机性)
            length_scale: 长度比例 (影响语速，越大越慢)

        Returns:
            str: 输出文件路径
        """
        import kaldi_native_fbank as knf

        # 确保模型已加载
        self._load_am_model()
        self._load_vocoder_model()
        pinyin_to_id = self._load_vocab()

        # 文本转token ID
        token_ids = self._split_and_process(text, pinyin_to_id)

        if not token_ids:
            raise ValueError("文本转换后无有效token")

        tokens = np.array([token_ids], dtype=np.int64)

        # 声学模型推理: token -> mel频谱
        x_lengths = np.array([tokens.shape[1]], dtype=np.int64)
        mel = self._am_model.run(
            [self._am_model.get_outputs()[0].name],
            {
                self._am_model.get_inputs()[0].name: tokens,
                self._am_model.get_inputs()[1].name: x_lengths,
                self._am_model.get_inputs()[2].name: np.array([noise_scale], dtype=np.float32),
                self._am_model.get_inputs()[3].name: np.array([length_scale], dtype=np.float32),
            },
        )[0]
        # mel: (batch_size, feat_dim, num_frames)

        # 声码器推理: mel -> 频谱
        mag, x, y = self._vocoder_model.run(
            [
                self._vocoder_model.get_outputs()[0].name,
                self._vocoder_model.get_outputs()[1].name,
                self._vocoder_model.get_outputs()[2].name,
            ],
            {
                self._vocoder_model.get_inputs()[0].name: mel,
            },
        )

        # ISTFT 重建音频
        stft_result = knf.StftResult(
            real=(mag * x)[0].transpose().reshape(-1).tolist(),
            imag=(mag * y)[0].transpose().reshape(-1).tolist(),
            num_frames=mag.shape[2],
        )
        config = knf.StftConfig(
            n_fft=1024,
            hop_length=256,
            win_length=1024,
            window_type="hann",
            center=True,
            pad_mode="reflect",
            normalized=False,
        )
        istft = knf.IStft(config)
        audio = np.array(istft(stft_result), dtype=np.float32)

        # 保存为 WAV
        sf.write(output_path, audio, self._sample_rate, "PCM_16")

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


def get_mixed_tts_engine() -> MixedTTSEngine:
    """获取中英混合 TTS 引擎实例"""
    global _mixed_engine
    if _mixed_engine is None:
        # 使用项目 models 目录下的模型
        project_root = Path(__file__).parent.parent.parent
        _mixed_engine = MixedTTSEngine(
            model_path=settings.mixed_tts_model if hasattr(settings, 'mixed_tts_model') else project_root / "models" / "model-steps-6.onnx",
            vocoder_path=settings.mixed_tts_vocoder if hasattr(settings, 'mixed_tts_vocoder') else project_root / "models" / "vocos-16khz-univ.onnx",
            vocab_path=settings.mixed_tts_vocab if hasattr(settings, 'mixed_tts_vocab') else project_root / "models" / "vocab_tts.txt",
        )
    return _mixed_engine
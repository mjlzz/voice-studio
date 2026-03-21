"""
悬浮话筒国际化支持
"""

from typing import Dict

# 支持的语言
SUPPORTED_LANGUAGES = {
    "zh-CN": "中文",
    "en-US": "English",
    "ja-JP": "日本語"
}

# 翻译字典
TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "zh-CN": {
        # 菜单
        "start_recording": "开始录音",
        "stop_recording": "停止录音",
        "processing": "处理中...",
        "transcription_mode": "转写模式",
        "streaming_mode": "实时流式",
        "batch_mode": "录音后转写",
        "copy_last_result": "复制最后结果",
        "clear_cache": "清除缓存",
        "hide_floating_button": "隐藏悬浮按钮",
        "show_floating_button": "显示悬浮按钮",
        "open_web": "打开网页",
        "quit": "退出",
        "language": "语言",

        # 通知
        "transcription_complete": "语音识别完成",
        "copied_to_clipboard": "已复制到剪贴板",
        "transcription_error": "语音识别错误",
        "copied": "已复制",
        "cleared": "已清除",
        "cache_cleared": "转写缓存已清空",
    },
    "en-US": {
        # Menu
        "start_recording": "Start Recording",
        "stop_recording": "Stop Recording",
        "processing": "Processing...",
        "transcription_mode": "Transcription Mode",
        "streaming_mode": "Real-time Streaming",
        "batch_mode": "Batch Transcription",
        "copy_last_result": "Copy Last Result",
        "clear_cache": "Clear Cache",
        "hide_floating_button": "Hide Floating Button",
        "show_floating_button": "Show Floating Button",
        "open_web": "Open Web",
        "quit": "Quit",
        "language": "Language",

        # Notifications
        "transcription_complete": "Transcription Complete",
        "copied_to_clipboard": "Copied to clipboard",
        "transcription_error": "Transcription Error",
        "copied": "Copied",
        "cleared": "Cleared",
        "cache_cleared": "Transcription cache cleared",
    },
    "ja-JP": {
        # メニュー
        "start_recording": "録音開始",
        "stop_recording": "録音停止",
        "processing": "処理中...",
        "transcription_mode": "認識モード",
        "streaming_mode": "リアルタイム",
        "batch_mode": "一括認識",
        "copy_last_result": "最後の結果をコピー",
        "clear_cache": "キャッシュをクリア",
        "hide_floating_button": "フローティングボタンを非表示",
        "show_floating_button": "フローティングボタンを表示",
        "open_web": "Webを開く",
        "quit": "終了",
        "language": "言語",

        # 通知
        "transcription_complete": "音声認識完了",
        "copied_to_clipboard": "クリップボードにコピーしました",
        "transcription_error": "音声認識エラー",
        "copied": "コピー完了",
        "cleared": "クリア完了",
        "cache_cleared": "認識キャッシュをクリアしました",
    }
}

# 当前语言
_current_language = "zh-CN"


def set_language(lang: str) -> None:
    """设置当前语言"""
    global _current_language
    if lang in SUPPORTED_LANGUAGES:
        _current_language = lang


def get_language() -> str:
    """获取当前语言"""
    return _current_language


def t(key: str, lang: str = None) -> str:
    """翻译文本"""
    language = lang or _current_language
    translations = TRANSLATIONS.get(language, TRANSLATIONS["zh-CN"])
    return translations.get(key, key)


def get_available_languages() -> Dict[str, str]:
    """获取可用语言列表"""
    return SUPPORTED_LANGUAGES.copy()
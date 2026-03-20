"""
Voice Studio CLI 工具
"""
import argparse
import asyncio
import sys
from pathlib import Path

from .config import settings
from .stt import get_stt_engine
from .tts import get_tts_engine, CHINESE_VOICES, ENGLISH_VOICES
from .api import run_server


def cmd_stt(args):
    """STT 命令"""
    engine = get_stt_engine()

    if args.file:
        # 文件转写
        result = engine.transcribe(
            args.file,
            language=args.language,
            word_timestamps=not args.no_words
        )

        print(f"\n检测语言: {result.language} (置信度: {result.language_prob})")
        print(f"处理耗时: {result.process_time}s | RTF: {result.rtf}")
        print("-" * 60)

        for seg in result.segments:
            start = _format_time(seg["start"])
            end = _format_time(seg["end"])
            print(f"[{start} → {end}]  {seg['text']}")

            if seg.get("words") and not args.no_words:
                word_line = "  词级: "
                for w in seg["words"]:
                    word_line += f"{w['word']}({w['start']:.2f}s) "
                print(word_line)

        # 导出
        if args.output:
            import json
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(result.model_dump(), f, ensure_ascii=False, indent=2)
            print(f"\n结果已保存: {args.output}")

    elif args.mic:
        # 实时麦克风转写 (TODO: 需要额外依赖)
        print("实时麦克风转写需要安装额外依赖: sounddevice, webrtcvad")
        print("请使用: pip install sounddevice webrtcvad")


def cmd_tts(args):
    """TTS 命令"""
    engine = get_tts_engine()

    # 确定音色
    voice = args.voice
    if voice in CHINESE_VOICES:
        voice = CHINESE_VOICES[voice]
    elif voice in ENGLISH_VOICES:
        voice = ENGLISH_VOICES[voice]

    # 获取文本
    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            text = f.read()
    else:
        text = args.text

    if not text.strip():
        print("错误: 文本不能为空")
        return

    # 输出路径
    output = args.output or str(settings.output_dir / "output.mp3")

    # 合成
    print(f"正在合成语音...")
    asyncio.run(engine.synthesize(
        text=text,
        output_path=output,
        voice=voice,
        rate=args.rate,
        volume=args.volume
    ))
    print(f"语音已保存: {output}")


def cmd_voices(args):
    """列出可用音色"""
    print("\n=== 中文预设音色 ===")
    for name, voice_id in CHINESE_VOICES.items():
        print(f"  {name}: {voice_id}")

    print("\n=== 英文预设音色 ===")
    for name, voice_id in ENGLISH_VOICES.items():
        print(f"  {name}: {voice_id}")

    if args.all:
        print("\n正在获取所有可用音色...")
        engine = get_tts_engine()
        voices = asyncio.run(engine.list_voices(args.lang))

        print(f"\n共 {len(voices)} 个音色:")
        for v in voices[:20]:  # 只显示前20个
            print(f"  [{v.locale}] {v.short_name} ({v.gender})")

        if len(voices) > 20:
            print(f"  ... 还有 {len(voices) - 20} 个音色")


def cmd_serve(args):
    """启动 API 服务"""
    print(f"启动 Voice Studio API 服务...")
    print(f"地址: http://{settings.host}:{settings.port}")
    print(f"文档: http://{settings.host}:{settings.port}/docs")
    run_server()


def _format_time(seconds: float) -> str:
    """格式化时间"""
    m, s = divmod(seconds, 60)
    return f"{int(m):02d}:{s:05.2f}"


def main():
    """CLI 主入口"""
    parser = argparse.ArgumentParser(
        prog="vs",
        description="Voice Studio - 让声音创作触手可及"
    )
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # stt 命令
    stt_parser = subparsers.add_parser("stt", help="语音转文字")
    stt_parser.add_argument("-i", "--file", help="音频文件路径")
    stt_parser.add_argument("-o", "--output", help="输出 JSON 文件路径")
    stt_parser.add_argument("-l", "--language", help="语言代码 (zh/en)")
    stt_parser.add_argument("--mic", action="store_true", help="实时麦克风转写")
    stt_parser.add_argument("--no-words", action="store_true", help="不显示词级时间戳")
    stt_parser.set_defaults(func=cmd_stt)

    # tts 命令
    tts_parser = subparsers.add_parser("tts", help="文字转语音")
    tts_parser.add_argument("-t", "--text", help="要合成的文本")
    tts_parser.add_argument("-f", "--file", help="文本文件路径")
    tts_parser.add_argument("-o", "--output", help="输出音频文件路径")
    tts_parser.add_argument("-v", "--voice", default="xiaoxiao", help="音色名称")
    tts_parser.add_argument("--rate", default="+0%", help="语速调节")
    tts_parser.add_argument("--volume", default="+0%", help="音量调节")
    tts_parser.set_defaults(func=cmd_tts)

    # voices 命令
    voices_parser = subparsers.add_parser("voices", help="列出可用音色")
    voices_parser.add_argument("--all", action="store_true", help="显示所有音色")
    voices_parser.add_argument("-l", "--lang", help="筛选语言")
    voices_parser.set_defaults(func=cmd_voices)

    # serve 命令
    serve_parser = subparsers.add_parser("serve", help="启动 API 服务")
    serve_parser.set_defaults(func=cmd_serve)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    args.func(args)


if __name__ == "__main__":
    main()
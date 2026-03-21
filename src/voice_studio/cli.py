"""
Voice Studio CLI 工具
"""
import argparse
import asyncio
import sys
import json
from pathlib import Path

from .config import settings
from .stt import get_stt_engine
from .tts import get_tts_engine, CHINESE_VOICES, ENGLISH_VOICES
from .tts_local import get_local_tts_engine, LOCAL_CHINESE_VOICES, LOCAL_ENGLISH_VOICES
from .api import run_server
from .process_manager import ProcessManager


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
    # 根据引擎选择音色映射和默认音色
    if args.engine == "local":
        voice_map = {**LOCAL_CHINESE_VOICES, **LOCAL_ENGLISH_VOICES}
        default_voice = "huayan"  # 本地默认音色
    else:
        voice_map = {**CHINESE_VOICES, **ENGLISH_VOICES}
        default_voice = "xiaoxiao"  # 云端默认音色

    # 确定音色
    voice = args.voice if args.voice != "xiaoxiao" or args.engine != "local" else default_voice
    if voice in voice_map:
        voice = voice_map[voice]

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
    if args.engine == "local":
        output = args.output or str(settings.output_dir / "output.wav")
    else:
        output = args.output or str(settings.output_dir / "output.mp3")

    # 合成
    print(f"正在合成语音 (引擎: {args.engine})...")

    if args.engine == "local":
        # 本地 Piper TTS
        engine = get_local_tts_engine()
        engine.synthesize(
            text=text,
            output_path=output,
            voice=voice
        )
    else:
        # 云端 edge-tts
        engine = get_tts_engine()
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
    print("\n=== 云端音色 (edge-tts) ===")
    print("\n中文预设:")
    for name, voice_id in CHINESE_VOICES.items():
        print(f"  {name}: {voice_id}")

    print("\n英文预设:")
    for name, voice_id in ENGLISH_VOICES.items():
        print(f"  {name}: {voice_id}")

    print("\n=== 本地音色 (piper-tts) ===")
    print("\n中文预设:")
    for name, voice_id in LOCAL_CHINESE_VOICES.items():
        print(f"  {name}: {voice_id}")

    print("\n英文预设:")
    for name, voice_id in LOCAL_ENGLISH_VOICES.items():
        print(f"  {name}: {voice_id}")

    if args.local:
        # 显示本地模型下载状态
        print("\n本地模型状态:")
        local_engine = get_local_tts_engine()
        voices = local_engine.list_voices()
        for v in voices:
            status = "✓ 已下载" if v["downloaded"] else "○ 未下载"
            print(f"  {status} {v['name']} ({v['language']}, {v['quality']})")

    if args.all:
        print("\n正在获取所有云端音色...")
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


# ========== 进程管理命令 ==========

def cmd_dev(args):
    """启动开发服务器（前后端一起）"""
    pm = ProcessManager()

    print("=" * 50)
    print("  Voice Studio 开发服务器")
    print("=" * 50)

    # 启动后端
    if not args.frontend_only:
        success, msg, pid = pm.start("backend")
        print(f"后端: {msg}")
        if not success:
            return

    # 启动前端
    if not args.backend_only:
        success, msg, pid = pm.start("frontend")
        print(f"前端: {msg}")
        if not success:
            if not args.frontend_only:
                pm.stop("backend")  # 回滚
            return

    print()
    print("-" * 50)
    print(f"  前端地址: http://localhost:{ProcessManager.FRONTEND_PORT}")
    print(f"  后端地址: http://localhost:{ProcessManager.BACKEND_PORT}")
    print(f"  API 文档: http://localhost:{ProcessManager.BACKEND_PORT}/docs")
    print("-" * 50)
    print("\n使用 'vs status' 查看状态")
    print("使用 'vs logs' 查看日志")
    print("使用 'vs stop' 停止服务")

    # 自动打开浏览器
    if args.open:
        import webbrowser
        webbrowser.open(f"http://localhost:{ProcessManager.FRONTEND_PORT}")


def cmd_status(args):
    """查看服务状态"""
    pm = ProcessManager()
    status = pm.get_all_status()

    if args.json:
        output = {name: info.to_dict() for name, info in status.items()}
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        print("\nVoice Studio 服务状态")
        print("=" * 50)
        print(f"{'服务':<10} {'端口':<8} {'状态':<12} {'PID':<8}")
        print("-" * 50)
        for name, info in status.items():
            pid_str = str(info.pid) if info.pid else "-"
            status_str = {
                "running": "运行中",
                "stopped": "已停止",
                "stale": "异常"
            }.get(info.status, info.status)
            print(f"{name:<10} {info.port:<8} {status_str:<12} {pid_str:<8}")
            if info.message:
                print(f"  └─ {info.message}")
        print("=" * 50)

        # 显示访问地址
        backend_running = status["backend"].status == "running"
        frontend_running = status["frontend"].status == "running"
        if backend_running or frontend_running:
            print("\n访问地址:")
            if frontend_running:
                print(f"  前端: http://localhost:{ProcessManager.FRONTEND_PORT}")
            if backend_running:
                print(f"  后端: http://localhost:{ProcessManager.BACKEND_PORT}")
                print(f"  文档: http://localhost:{ProcessManager.BACKEND_PORT}/docs")


def cmd_stop(args):
    """停止服务"""
    pm = ProcessManager()

    if not args.frontend_only:
        success, msg = pm.stop("backend")
        status = "✓" if success else "✗"
        print(f"{status} 后端: {msg}")

    if not args.backend_only:
        success, msg = pm.stop("frontend")
        status = "✓" if success else "✗"
        print(f"{status} 前端: {msg}")

    print("服务已停止")


def cmd_restart(args):
    """重启服务"""
    pm = ProcessManager()

    print("正在重启服务...")

    if not args.frontend_only:
        success, msg, pid = pm.restart("backend")
        status = "✓" if success else "✗"
        print(f"{status} 后端: {msg}")

    if not args.backend_only:
        success, msg, pid = pm.restart("frontend")
        status = "✓" if success else "✗"
        print(f"{status} 前端: {msg}")

    print("\n访问地址: http://localhost:2345")


def cmd_logs(args):
    """查看日志"""
    pm = ProcessManager()

    if args.follow:
        name = "backend" if args.backend else "frontend" if args.frontend else None
        if name:
            print(f"跟踪 {name} 日志 (按 Ctrl+C 退出)...")
            print("-" * 50)
            try:
                pm.tail_logs(name)
            except KeyboardInterrupt:
                print("\n已退出")
        else:
            print("实时跟踪日志请指定 --backend 或 --frontend")
    else:
        if args.backend or not args.frontend:
            print("=== 后端日志 ===")
            print(pm.read_logs("backend", args.lines))
        if args.frontend or (not args.backend and not args.frontend):
            if not args.backend:
                print("\n=== 前端日志 ===")
                print(pm.read_logs("frontend", args.lines))


def cmd_mic(args):
    """启动悬浮话筒"""
    from .floating_mic import main as floating_mic_main
    print("启动悬浮话筒...")
    print("提示: 请确保后端服务已启动 (vs serve 或 vs dev)")
    print("-" * 50)
    floating_mic_main()


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
    tts_parser.add_argument("--engine", choices=["cloud", "local"], default="cloud",
                            help="TTS引擎: cloud(edge-tts在线) 或 local(piper离线)")
    tts_parser.add_argument("--rate", default="+0%", help="语速调节 (仅cloud)")
    tts_parser.add_argument("--volume", default="+0%", help="音量调节 (仅cloud)")
    tts_parser.set_defaults(func=cmd_tts)

    # voices 命令
    voices_parser = subparsers.add_parser("voices", help="列出可用音色")
    voices_parser.add_argument("--all", action="store_true", help="显示所有云端音色")
    voices_parser.add_argument("--local", action="store_true", help="显示本地模型状态")
    voices_parser.add_argument("-l", "--lang", help="筛选语言")
    voices_parser.set_defaults(func=cmd_voices)

    # serve 命令
    serve_parser = subparsers.add_parser("serve", help="启动 API 服务")
    serve_parser.set_defaults(func=cmd_serve)

    # dev 命令
    dev_parser = subparsers.add_parser("dev", help="启动开发服务器（前后端一起）")
    dev_parser.add_argument("--backend-only", action="store_true", help="仅启动后端")
    dev_parser.add_argument("--frontend-only", action="store_true", help="仅启动前端")
    dev_parser.add_argument("--open", "-o", action="store_true", help="自动打开浏览器")
    dev_parser.set_defaults(func=cmd_dev)

    # status 命令
    status_parser = subparsers.add_parser("status", help="查看服务状态")
    status_parser.add_argument("--json", action="store_true", help="JSON 格式输出")
    status_parser.set_defaults(func=cmd_status)

    # stop 命令
    stop_parser = subparsers.add_parser("stop", help="停止服务")
    stop_parser.add_argument("--backend-only", action="store_true", help="仅停止后端")
    stop_parser.add_argument("--frontend-only", action="store_true", help="仅停止前端")
    stop_parser.set_defaults(func=cmd_stop)

    # restart 命令
    restart_parser = subparsers.add_parser("restart", help="重启服务")
    restart_parser.add_argument("--backend-only", action="store_true", help="仅重启后端")
    restart_parser.add_argument("--frontend-only", action="store_true", help="仅重启前端")
    restart_parser.set_defaults(func=cmd_restart)

    # logs 命令
    logs_parser = subparsers.add_parser("logs", help="查看日志")
    logs_parser.add_argument("--backend", action="store_true", help="查看后端日志")
    logs_parser.add_argument("--frontend", action="store_true", help="查看前端日志")
    logs_parser.add_argument("-n", "--lines", type=int, default=50, help="显示行数")
    logs_parser.add_argument("-f", "--follow", action="store_true", help="实时跟踪日志")
    logs_parser.set_defaults(func=cmd_logs)

    # mic 命令
    mic_parser = subparsers.add_parser("mic", help="启动悬浮话筒")
    mic_parser.set_defaults(func=cmd_mic)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    args.func(args)


if __name__ == "__main__":
    main()
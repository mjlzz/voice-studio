"""
Voice Studio 进程管理模块

提供跨平台的进程管理功能：
- PID 文件管理
- 端口冲突检测
- 进程启动/停止/重启
- 日志管理
"""
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional, Tuple, List
from datetime import datetime
import subprocess
import sys
import os
import signal
import socket
import time
import shutil


@dataclass
class ProcessInfo:
    """进程信息"""
    name: str           # backend / frontend
    pid: int
    port: int
    status: str         # running / stopped / stale
    message: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class PortCheckResult:
    """端口检测结果"""
    available: bool
    occupied_by_self: bool = False   # 是否被本服务占用
    occupied_pid: Optional[int] = None
    occupied_process: Optional[str] = None  # 进程名


class ProcessManager:
    """跨平台进程管理器"""

    BACKEND_PORT = 8765
    FRONTEND_PORT = 2345
    BACKEND_KEYWORD = "voice_studio"  # 后端进程关键字
    FRONTEND_KEYWORD = "vite"         # 前端进程关键字

    def __init__(self):
        self.run_dir = Path.home() / ".voicestudio"
        self.run_dir.mkdir(parents=True, exist_ok=True)

    # ========== PID 文件管理 ==========

    def _pid_file(self, name: str) -> Path:
        """PID 文件路径"""
        return self.run_dir / f"{name}.pid"

    def _log_file(self, name: str) -> Path:
        """日志文件路径"""
        return self.run_dir / f"{name}.log"

    def _read_pid(self, name: str) -> Optional[int]:
        """读取 PID"""
        pid_file = self._pid_file(name)
        if pid_file.exists():
            try:
                return int(pid_file.read_text().strip())
            except ValueError:
                return None
        return None

    def _write_pid(self, name: str, pid: int):
        """写入 PID"""
        self._pid_file(name).write_text(str(pid))

    def _remove_pid(self, name: str):
        """删除 PID 文件"""
        self._pid_file(name).unlink(missing_ok=True)

    # ========== 端口检测 ==========

    def _is_port_listening(self, port: int) -> bool:
        """检查端口是否被监听（支持 IPv4 和 IPv6）"""
        # 检查 IPv4
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex(("127.0.0.1", port))
                if result == 0:
                    return True
        except Exception:
            pass

        # 检查 IPv6
        try:
            with socket.socket(socket.AF_INET6, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex(("::1", port))
                if result == 0:
                    return True
        except Exception:
            pass

        return False

    def _get_pid_by_port(self, port: int) -> Optional[int]:
        """获取占用端口的 PID"""
        if sys.platform == "win32":
            # Windows: netstat -ano
            try:
                result = subprocess.run(
                    ["netstat", "-ano"],
                    capture_output=True, text=True, timeout=10
                )
                for line in result.stdout.split("\n"):
                    if f":{port}" in line and "LISTENING" in line:
                        parts = line.split()
                        if len(parts) >= 5:
                            try:
                                return int(parts[-1])
                            except ValueError:
                                pass
            except Exception:
                pass
        else:
            # Unix: lsof -i :PORT -t
            try:
                result = subprocess.run(
                    ["lsof", "-i", f":{port}", "-t"],
                    capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0 and result.stdout.strip():
                    return int(result.stdout.strip().split()[0])
            except Exception:
                pass
        return None

    def _get_process_command(self, pid: int) -> str:
        """获取进程命令行"""
        try:
            if sys.platform == "win32":
                result = subprocess.run(
                    ["wmic", "process", "where", f"ProcessId={pid}",
                     "get", "CommandLine", "/VALUE"],
                    capture_output=True, text=True, timeout=10
                )
                return result.stdout.lower()
            else:
                result = subprocess.run(
                    ["ps", "-p", str(pid), "-o", "command="],
                    capture_output=True, text=True, timeout=10
                )
                return result.stdout.lower()
        except Exception:
            return ""

    def _get_process_name(self, pid: int) -> str:
        """获取进程名"""
        try:
            if sys.platform == "win32":
                result = subprocess.run(
                    ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
                    capture_output=True, text=True, timeout=10
                )
                lines = result.stdout.strip().split("\n")
                if lines:
                    parts = lines[0].split()
                    if parts:
                        return parts[0]
                return "unknown"
            else:
                result = subprocess.run(
                    ["ps", "-p", str(pid), "-o", "comm="],
                    capture_output=True, text=True, timeout=10
                )
                return result.stdout.strip() or "unknown"
        except Exception:
            return "unknown"

    def check_port(self, name: str, port: int) -> PortCheckResult:
        """
        检查端口状态

        Returns:
            PortCheckResult:
                - available=True: 端口空闲
                - available=False, occupied_by_self=True: 被本服务占用
                - available=False, occupied_by_self=False: 被其他服务占用
        """
        if not self._is_port_listening(port):
            return PortCheckResult(available=True)

        # 端口被占用，检查是谁占用
        pid = self._get_pid_by_port(port)

        # 如果找不到 PID，可能是 TIME_WAIT 状态，认为端口可用
        if pid is None:
            return PortCheckResult(available=True)

        # 检查该 PID 的进程是否真的在运行
        if not self._is_process_running(pid):
            # 进程不存在，可能是残留的端口状态，认为端口可用
            return PortCheckResult(available=True)

        # 检查是否是本服务的 PID
        stored_pid = self._read_pid(name)
        if stored_pid and stored_pid == pid:
            return PortCheckResult(
                available=False,
                occupied_by_self=True,
                occupied_pid=pid
            )

        # 检查进程命令行
        cmd = self._get_process_command(pid)
        keyword = self.BACKEND_KEYWORD if name == "backend" else self.FRONTEND_KEYWORD
        if keyword in cmd:
            return PortCheckResult(
                available=False,
                occupied_by_self=True,
                occupied_pid=pid
            )

        # 被其他服务占用
        return PortCheckResult(
            available=False,
            occupied_by_self=False,
            occupied_pid=pid,
            occupied_process=self._get_process_name(pid)
        )

    # ========== 进程状态 ==========

    def _is_process_running(self, pid: int) -> bool:
        """检查进程是否在运行"""
        if sys.platform == "win32":
            try:
                result = subprocess.run(
                    ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
                    capture_output=True, text=True, timeout=5
                )
                return str(pid) in result.stdout
            except Exception:
                return False
        else:
            try:
                os.kill(pid, 0)
                return True
            except OSError:
                return False

    def get_process_info(self, name: str) -> ProcessInfo:
        """获取进程信息"""
        pid = self._read_pid(name)
        port = self.BACKEND_PORT if name == "backend" else self.FRONTEND_PORT

        if pid is None:
            return ProcessInfo(name=name, pid=0, port=port, status="stopped")

        if self._is_process_running(pid):
            # 进程存在，检查端口
            if self._is_port_listening(port):
                return ProcessInfo(name=name, pid=pid, port=port, status="running")
            else:
                return ProcessInfo(
                    name=name, pid=pid, port=port, status="running",
                    message="进程存在但端口未监听"
                )
        else:
            # PID 文件存在但进程不存在，清理陈旧文件
            self._remove_pid(name)
            return ProcessInfo(name=name, pid=pid, port=port, status="stale")

    def get_all_status(self) -> dict:
        """获取所有服务状态"""
        return {
            "backend": self.get_process_info("backend"),
            "frontend": self.get_process_info("frontend"),
        }

    # ========== 进程启动 ==========

    def _find_npm(self) -> str:
        """查找 npm"""
        for name in ["npm.cmd", "npm"]:
            path = shutil.which(name)
            if path:
                return path
        raise RuntimeError("未找到 npm，请确保 Node.js 已安装并添加到 PATH")

    def _start_process(self, name: str) -> Optional[int]:
        """启动进程"""
        log_path = self._log_file(name)
        log_file = open(log_path, "w", encoding="utf-8")

        project_root = Path(__file__).parent.parent.parent

        if name == "backend":
            cmd = [sys.executable, "-m", "voice_studio.cli", "serve"]
            cwd = project_root
        else:
            # 前端：直接使用 node 运行 vite，避免批处理文件的子进程问题
            node_exe = shutil.which("node")
            if not node_exe:
                raise RuntimeError("未找到 node，请确保 Node.js 已安装并添加到 PATH")

            vite_js = project_root / "web" / "node_modules" / "vite" / "bin" / "vite.js"
            if not vite_js.exists():
                raise RuntimeError(f"未找到 vite.js，请先在 web 目录运行 npm install")

            cmd = [node_exe, str(vite_js)]
            cwd = project_root / "web"

        try:
            if sys.platform == "win32":
                proc = subprocess.Popen(
                    cmd,
                    cwd=str(cwd),
                    stdout=log_file,
                    stderr=log_file,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                )
            else:
                proc = subprocess.Popen(
                    cmd,
                    cwd=str(cwd),
                    stdout=log_file,
                    stderr=log_file,
                    start_new_session=True
                )

            self._write_pid(name, proc.pid)
            return proc.pid
        except Exception as e:
            print(f"启动失败: {e}")
            return None

    def start(self, name: str) -> Tuple[bool, str, Optional[int]]:
        """
        启动服务

        Returns:
            (success, message, pid)
        """
        port = self.BACKEND_PORT if name == "backend" else self.FRONTEND_PORT

        # 检查端口
        check = self.check_port(name, port)

        if not check.available:
            if check.occupied_by_self:
                # 本服务占用，自动关闭
                print(f"端口 {port} 已被本服务占用 (PID: {check.occupied_pid})，正在关闭...")
                self._kill_process(check.occupied_pid)
                self._remove_pid(name)
                time.sleep(1)  # 等待端口释放
            else:
                # 其他服务占用，报错
                return False, (
                    f"端口 {port} 已被其他服务占用 "
                    f"(PID: {check.occupied_pid}, 进程: {check.occupied_process})，"
                    f"请手动关闭该服务"
                ), None

        # 启动进程
        pid = self._start_process(name)
        if pid:
            # 等待一下确认启动成功
            time.sleep(2)
            if self._is_process_running(pid):
                return True, f"启动成功 (PID: {pid})", pid
            else:
                return False, "启动失败，进程已退出，请查看日志", pid
        else:
            return False, "启动失败", None

    # ========== 进程停止 ==========

    def _kill_process(self, pid: int) -> bool:
        """终止进程"""
        try:
            if sys.platform == "win32":
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(pid)],
                    capture_output=True, timeout=10
                )
            else:
                try:
                    os.killpg(os.getpgid(pid), signal.SIGTERM)
                except (ProcessLookupError, PermissionError):
                    pass
            return True
        except Exception:
            return False

    def stop(self, name: str) -> Tuple[bool, str]:
        """停止服务"""
        pid = self._read_pid(name)
        if pid is None:
            return True, "服务未运行"

        if self._kill_process(pid):
            self._remove_pid(name)
            return True, f"已停止 (PID: {pid})"
        else:
            return False, f"停止失败 (PID: {pid})"

    def stop_all(self) -> dict:
        """停止所有服务"""
        return {
            "backend": self.stop("backend"),
            "frontend": self.stop("frontend"),
        }

    # ========== 进程重启 ==========

    def restart(self, name: str) -> Tuple[bool, str, Optional[int]]:
        """重启服务"""
        self.stop(name)
        time.sleep(1)
        return self.start(name)

    def restart_all(self) -> dict:
        """重启所有服务"""
        return {
            "backend": self.restart("backend"),
            "frontend": self.restart("frontend"),
        }

    # ========== 日志管理 ==========

    def read_logs(self, name: str, lines: int = 50) -> str:
        """读取日志"""
        log_file = self._log_file(name)
        if not log_file.exists():
            return "日志文件不存在"
        try:
            with open(log_file, "r", encoding="utf-8", errors="replace") as f:
                all_lines = f.readlines()
                return "".join(all_lines[-lines:])
        except Exception as e:
            return f"读取日志失败: {e}"

    def tail_logs(self, name: str):
        """实时跟踪日志"""
        log_file = self._log_file(name)
        if not log_file.exists():
            print("等待日志文件生成...")
            while not log_file.exists():
                time.sleep(0.5)

        with open(log_file, "r", encoding="utf-8", errors="replace") as f:
            # 先显示已有内容
            f.seek(0, 2)  # 跳到文件末尾

            while True:
                line = f.readline()
                if line:
                    print(line, end="", flush=True)
                else:
                    time.sleep(0.1)

    def clear_logs(self, name: str):
        """清空日志"""
        log_file = self._log_file(name)
        if log_file.exists():
            log_file.unlink()
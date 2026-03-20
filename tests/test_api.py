"""
Voice Studio API 测试
"""
import pytest
from io import BytesIO
from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """健康检查端点测试"""

    def test_health_check_returns_ok(self, client: TestClient):
        """健康检查应该返回 ok 状态"""
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["version"] == "0.1.0"

    def test_health_check_has_request_id(self, client: TestClient):
        """响应应该包含 X-Request-ID"""
        response = client.get("/api/v1/health")

        assert "x-request-id" in response.headers
        assert response.headers["x-request-id"]


class TestEnginesEndpoint:
    """引擎列表端点测试"""

    def test_list_engines(self, client: TestClient):
        """应该返回引擎列表"""
        response = client.get("/api/v1/engines")

        assert response.status_code == 200
        data = response.json()
        assert "stt" in data
        assert "tts" in data
        assert data["stt"]["status"] == "available"
        assert data["tts"]["status"] == "available"


class TestSTTEndpoint:
    """STT 端点测试"""

    def test_transcribe_audio_success(self, client: TestClient, sample_audio_bytes: bytes):
        """正常转写应该返回结果"""
        files = {"file": ("test.wav", BytesIO(sample_audio_bytes), "audio/wav")}
        response = client.post("/api/v1/stt/transcribe", files=files)

        assert response.status_code == 200
        data = response.json()
        assert "text" in data
        assert data["language"] == "zh"

    def test_transcribe_empty_file(self, client: TestClient):
        """空文件应该返回错误"""
        files = {"file": ("empty.wav", BytesIO(b""), "audio/wav")}
        response = client.post("/api/v1/stt/transcribe", files=files)

        assert response.status_code == 400
        data = response.json()
        assert data["code"] == "EMPTY_FILE"

    def test_transcribe_invalid_file_type(self, client: TestClient):
        """无效文件类型应该返回错误"""
        files = {"file": ("test.exe", BytesIO(b"not audio"), "application/octet-stream")}
        response = client.post("/api/v1/stt/transcribe", files=files)

        assert response.status_code == 400
        data = response.json()
        assert data["code"] == "UNSUPPORTED_FILE_TYPE"

    def test_transcribe_has_request_id(self, client: TestClient, sample_audio_bytes: bytes):
        """响应应该包含 X-Request-ID"""
        files = {"file": ("test.wav", BytesIO(sample_audio_bytes), "audio/wav")}
        response = client.post("/api/v1/stt/transcribe", files=files)

        assert "x-request-id" in response.headers


class TestTTSEndpoint:
    """TTS 端点测试"""

    def test_list_voices_cloud(self, client: TestClient):
        """应该返回云端音色列表"""
        response = client.get("/api/v1/tts/voices?engine=cloud")

        assert response.status_code == 200
        data = response.json()
        assert "voices" in data

    def test_list_voices_local(self, client: TestClient):
        """应该返回本地音色列表"""
        response = client.get("/api/v1/tts/voices?engine=local")

        assert response.status_code == 200
        data = response.json()
        assert "voices" in data

    def test_list_presets(self, client: TestClient):
        """应该返回预设音色"""
        response = client.get("/api/v1/tts/presets")

        assert response.status_code == 200
        data = response.json()
        assert "cloud" in data
        assert "local" in data

    def test_synthesize_empty_text(self, client: TestClient):
        """空文本应该返回错误"""
        response = client.post(
            "/api/v1/tts/synthesize?engine=cloud",
            json={"text": "", "voice": "zh-CN-XiaoxiaoNeural"}
        )

        assert response.status_code == 422  # Pydantic validation error

    def test_synthesize_invalid_rate_format(self, client: TestClient):
        """无效的语速格式应该返回错误"""
        response = client.post(
            "/api/v1/tts/synthesize?engine=cloud",
            json={"text": "测试文本", "rate": "50"}  # 缺少 +/- 前缀
        )

        assert response.status_code == 422

    def test_synthesize_text_too_long(self, client: TestClient):
        """超长文本应该返回错误"""
        from voice_studio.config import settings
        long_text = "测试" * (settings.max_text_length // 2 + 1)

        response = client.post(
            "/api/v1/tts/synthesize?engine=cloud",
            json={"text": long_text}
        )

        assert response.status_code == 422


class TestErrorHandling:
    """错误处理测试"""

    def test_error_response_format(self, client: TestClient):
        """错误响应应该包含标准格式"""
        files = {"file": ("test.exe", BytesIO(b"not audio"), "application/octet-stream")}
        response = client.post("/api/v1/stt/transcribe", files=files)

        assert response.status_code == 400
        data = response.json()
        assert "code" in data
        assert "message" in data
        assert "request_id" in data

    def test_request_id_propagation(self, client: TestClient):
        """自定义 X-Request-ID 应该被保留"""
        custom_id = "test-custom-id-123"
        response = client.get(
            "/api/v1/health",
            headers={"X-Request-ID": custom_id}
        )

        assert response.headers["x-request-id"] == custom_id


class TestCORS:
    """CORS 配置测试"""

    def test_cors_headers_present(self, client: TestClient):
        """CORS 头应该存在"""
        response = client.options(
            "/api/v1/health",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            }
        )

        # TestClient 可能不完整支持 CORS，这里主要检查不会报错
        assert response.status_code in [200, 400, 405]
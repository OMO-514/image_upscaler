"""
ncnn-Vulkan 版 Real-ESRGAN / waifu2x をローカル subprocess で呼び出すラッパ。
外部API・ネットワーク通信は行わない。
"""
from __future__ import annotations

import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

BASE_DIR = Path(__file__).resolve().parent
BIN_DIR = BASE_DIR / "bin"

REALESRGAN_DIR = BIN_DIR / "realesrgan-ncnn-vulkan"
WAIFU2X_DIR = BIN_DIR / "waifu2x-ncnn-vulkan"

REALESRGAN_EXE = REALESRGAN_DIR / "realesrgan-ncnn-vulkan.exe"
WAIFU2X_EXE = WAIFU2X_DIR / "waifu2x-ncnn-vulkan.exe"

EngineName = Literal["realesrgan-photo", "realesrgan-anime", "waifu2x"]

REALESRGAN_MODELS = {
    "realesrgan-photo": "realesrgan-x4plus",
    "realesrgan-anime": "realesrgan-x4plus-anime",
}


@dataclass
class UpscaleResult:
    output_path: Path
    elapsed_sec: float
    engine: str
    scale: int
    stdout: str
    stderr: str


class EngineNotFoundError(RuntimeError):
    pass


def check_engine(engine: EngineName) -> tuple[bool, str]:
    """エンジンバイナリが配置済みか確認。"""
    if engine in ("realesrgan-photo", "realesrgan-anime"):
        exe = REALESRGAN_EXE
        # Real-ESRGAN: models/realesrgan-x4plus.bin など
        model_marker = REALESRGAN_DIR / "models" / f"{REALESRGAN_MODELS[engine]}.bin"
        if not exe.exists():
            return False, f"バイナリ未配置: {exe}"
        if not model_marker.exists():
            return False, f"モデル未配置: {model_marker}"
    elif engine == "waifu2x":
        exe = WAIFU2X_EXE
        # waifu2x: models-cunet/ などのサブフォルダ群
        model_marker = WAIFU2X_DIR / "models-cunet"
        if not exe.exists():
            return False, f"バイナリ未配置: {exe}"
        if not model_marker.exists():
            return False, f"モデル未配置: {model_marker}"
    else:
        return False, f"未知のエンジン: {engine}"

    return True, "OK"


def upscale(
    input_path: Path,
    output_path: Path,
    engine: EngineName = "realesrgan-photo",
    scale: int = 4,
    noise: int = 0,
    tta: bool = False,
    output_format: str = "png",
) -> UpscaleResult:
    """
    画像を高画質化して output_path に保存する。

    Args:
        input_path: 入力画像
        output_path: 出力先
        engine: realesrgan-photo / realesrgan-anime / waifu2x
        scale: 倍率（Real-ESRGAN=4固定、waifu2x=1/2/4）
        noise: ノイズ除去レベル（waifu2x: -1〜3）
        tta: Test-Time Augmentation（精度↑だが処理時間8倍）
        output_format: png / jpg / webp
    """
    ok, msg = check_engine(engine)
    if not ok:
        raise EngineNotFoundError(msg)

    input_path = Path(input_path).resolve()
    output_path = Path(output_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if engine.startswith("realesrgan"):
        cmd = [
            str(REALESRGAN_EXE),
            "-i", str(input_path),
            "-o", str(output_path),
            "-n", REALESRGAN_MODELS[engine],
            "-s", str(scale),
            "-f", output_format,
        ]
        if tta:
            cmd.append("-x")
        cwd = REALESRGAN_DIR
    else:  # waifu2x
        cmd = [
            str(WAIFU2X_EXE),
            "-i", str(input_path),
            "-o", str(output_path),
            "-n", str(noise),
            "-s", str(scale),
            "-m", "models-cunet",
            "-f", output_format,
        ]
        if tta:
            cmd.append("-x")
        cwd = WAIFU2X_DIR

    start = time.time()
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )
    elapsed = time.time() - start

    if proc.returncode != 0 or not output_path.exists():
        raise RuntimeError(
            f"アップスケール失敗 (exit={proc.returncode})\n"
            f"STDOUT: {proc.stdout}\nSTDERR: {proc.stderr}"
        )

    return UpscaleResult(
        output_path=output_path,
        elapsed_sec=elapsed,
        engine=engine,
        scale=scale,
        stdout=proc.stdout,
        stderr=proc.stderr,
    )


def engine_status() -> dict[str, tuple[bool, str]]:
    """全エンジンの導入状況を返す。"""
    return {
        "realesrgan-photo": check_engine("realesrgan-photo"),
        "realesrgan-anime": check_engine("realesrgan-anime"),
        "waifu2x": check_engine("waifu2x"),
    }

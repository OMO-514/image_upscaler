"""
画像高画質化ツール - Streamlit GUI
完全ローカル処理。外部API・クラウド送信なし。
"""
from __future__ import annotations

import io
import shutil
import uuid
from datetime import datetime
from pathlib import Path

import streamlit as st
from PIL import Image

from upscaler import (
    EngineNotFoundError,
    engine_status,
    upscale,
)

BASE_DIR = Path(__file__).resolve().parent
TEMP_DIR = BASE_DIR / "temp"
OUTPUT_DIR = BASE_DIR / "output"
TEMP_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

st.set_page_config(
    page_title="画像高画質化ツール",
    page_icon="🖼️",
    layout="wide",
)

# ---------- スタイル ----------
st.markdown(
    """
    <style>
    .privacy-badge {
        background: #1e3a2e;
        border-left: 4px solid #4ade80;
        padding: 0.6rem 0.9rem;
        border-radius: 4px;
        font-size: 0.85rem;
        margin-bottom: 1rem;
    }
    .metric-box { background: #1f2937; padding: 0.8rem; border-radius: 6px; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🖼️ 画像高画質化ツール")
st.markdown(
    '<div class="privacy-badge">🔒 <b>完全ローカル処理</b>: '
    'すべての処理はこのPC内で完結します。画像はインターネット上に送信されません。</div>',
    unsafe_allow_html=True,
)

# ---------- サイドバー: エンジン状態 ----------
with st.sidebar:
    st.header("⚙️ 設定")

    status = engine_status()
    ready_engines = [name for name, (ok, _) in status.items() if ok]

    if not ready_engines:
        st.error(
            "❌ エンジンバイナリが未配置です。\n\n"
            "README.md の手順に従い、`bin/` フォルダにダウンロードしてください。"
        )
        with st.expander("📋 エンジン状態 詳細"):
            for name, (ok, msg) in status.items():
                icon = "✅" if ok else "❌"
                st.text(f"{icon} {name}: {msg}")
        st.stop()

    engine_label_map = {
        "realesrgan-photo": "📷 Real-ESRGAN (写真向け)",
        "realesrgan-anime": "🎨 Real-ESRGAN (イラスト向け)",
        "waifu2x": "✨ waifu2x (アニメ/イラスト)",
    }
    engine_options = {engine_label_map[e]: e for e in ready_engines}
    selected_label = st.selectbox(
        "エンジン",
        list(engine_options.keys()),
        help="写真→Real-ESRGAN photo / イラスト→Real-ESRGAN anime か waifu2x",
    )
    engine = engine_options[selected_label]

    if engine.startswith("realesrgan"):
        scale = st.select_slider("拡大倍率", options=[4], value=4, help="Real-ESRGANは4倍固定")
        noise = 0
    else:
        scale = st.select_slider("拡大倍率", options=[1, 2, 4], value=2)
        noise = st.select_slider(
            "ノイズ除去レベル",
            options=[-1, 0, 1, 2, 3],
            value=1,
            help="-1: 無効, 0-3: 強度（数値が大きいほど強い）",
        )

    output_format = st.selectbox("出力形式", ["png", "jpg", "webp"], index=0)
    tta = st.checkbox(
        "TTA モード (高精度・8倍遅い)",
        value=False,
        help="精度向上のため8方向で処理。処理時間が約8倍に。",
    )

    st.divider()
    st.subheader("🔒 プライバシー")
    auto_delete = st.checkbox(
        "処理後に入力ファイルを自動削除",
        value=True,
        help="temp/ フォルダの入力画像を処理完了後に削除します。",
    )
    save_to_output = st.checkbox(
        "output/ フォルダにも保存",
        value=True,
        help="ダウンロードと別にプロジェクト内に履歴として保存します。",
    )

# ---------- メイン: アップロード ----------
col_upload, col_info = st.columns([2, 1])

with col_upload:
    uploaded = st.file_uploader(
        "画像をドラッグ&ドロップ または クリックで選択",
        type=["png", "jpg", "jpeg", "webp", "bmp"],
        help="最大200MB。RAW非対応。",
    )

with col_info:
    if uploaded is not None:
        img = Image.open(uploaded)
        st.markdown(f"**ファイル名**: `{uploaded.name}`")
        st.markdown(f"**サイズ**: {img.width} × {img.height} px")
        st.markdown(f"**形式**: {img.format}")
        size_kb = len(uploaded.getvalue()) / 1024
        st.markdown(f"**容量**: {size_kb:,.1f} KB")
        out_w, out_h = img.width * scale, img.height * scale
        st.markdown(f"**出力予定**: {out_w} × {out_h} px")
        uploaded.seek(0)

if uploaded is None:
    st.info("👆 画像をアップロードしてください。")
    st.stop()

# ---------- 実行 ----------
st.divider()
run = st.button("🚀 高画質化を実行", type="primary", use_container_width=True)

if run:
    # 入力ファイル一時保存
    session_id = uuid.uuid4().hex[:8]
    suffix = Path(uploaded.name).suffix or ".png"
    in_path = TEMP_DIR / f"in_{session_id}{suffix}"
    in_path.write_bytes(uploaded.getvalue())

    out_name = f"{Path(uploaded.name).stem}_x{scale}_{engine}.{output_format}"
    out_path = TEMP_DIR / f"out_{session_id}_{out_name}"

    with st.spinner(f"🔧 {engine} で処理中... (CPU/GPUによっては時間がかかります)"):
        try:
            result = upscale(
                in_path,
                out_path,
                engine=engine,
                scale=scale,
                noise=noise,
                tta=tta,
                output_format=output_format,
            )
        except EngineNotFoundError as e:
            st.error(f"❌ エンジン未配置: {e}")
            st.stop()
        except RuntimeError as e:
            st.error(f"❌ 処理失敗: {e}")
            st.stop()

    st.success(f"✅ 完了！ 処理時間: {result.elapsed_sec:.1f}秒")

    # output/ にコピー
    saved_path = None
    if save_to_output:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        saved_path = OUTPUT_DIR / f"{timestamp}_{out_name}"
        shutil.copy(out_path, saved_path)

    # プレビュー
    st.subheader("📊 Before / After")
    try:
        from streamlit_image_comparison import image_comparison
        image_comparison(
            img1=str(in_path),
            img2=str(out_path),
            label1="Before",
            label2="After",
            width=900,
            in_memory=True,
        )
    except ImportError:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Before**")
            st.image(str(in_path), use_column_width=True)
        with c2:
            st.markdown("**After**")
            st.image(str(out_path), use_column_width=True)

    # メトリクス
    out_img = Image.open(out_path)
    in_size_kb = in_path.stat().st_size / 1024
    out_size_kb = out_path.stat().st_size / 1024
    m1, m2, m3 = st.columns(3)
    m1.metric("出力解像度", f"{out_img.width} × {out_img.height}")
    m2.metric("ファイルサイズ", f"{out_size_kb:,.1f} KB", delta=f"{out_size_kb - in_size_kb:+,.1f} KB")
    m3.metric("処理時間", f"{result.elapsed_sec:.1f} 秒")

    # ダウンロード
    with open(out_path, "rb") as f:
        st.download_button(
            "⬇️ 高画質画像をダウンロード",
            data=f.read(),
            file_name=out_name,
            mime=f"image/{output_format}",
            type="primary",
            use_container_width=True,
        )

    if saved_path:
        st.caption(f"💾 ローカル保存先: `{saved_path}`")

    # 入力ファイル削除
    if auto_delete:
        try:
            in_path.unlink(missing_ok=True)
            out_path.unlink(missing_ok=True)
            st.caption("🗑️ temp/ の作業ファイルを削除しました。")
        except Exception as e:
            st.warning(f"削除失敗: {e}")

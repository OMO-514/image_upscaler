# 🖼️ 画像高画質化ツール (Image Upscaler)

写真・イラストをAI超解像で高画質化する**完全ローカル**のStreamlit GUIツール。

## 🔒 プライバシー方針

- **完全ローカル処理**: 画像はインターネット上に一切送信されません
- **外部API不使用**: Real-ESRGAN / waifu2x の **ncnn-Vulkan版** をローカル実行
- **localhost束縛**: Streamlitは `127.0.0.1` のみで待ち受け（LAN/外部から到達不可）
- **テレメトリ無効**: Streamlitの使用統計送信OFF
- **自動削除オプション**: 処理後に作業ファイルを自動削除可能

## 📋 動作環境

- Windows 10/11
- Python 3.10+（3.14 で動作確認）
- AMD Radeon / NVIDIA / Intel GPU いずれも対応（Vulkan経由でGPU加速）
- GPUなし CPU でも動作可（やや遅い）

## 🚀 かんたんスタート（おすすめ・2ステップ）

### 1. ダウンロード

このページ上部の緑の **「Code」→「Download ZIP」** をクリックして、解凍します。
（Gitを使う方は `git clone https://github.com/OMO-514/image_upscaler.git`）

### 2. `start.bat` をダブルクリック

解凍したフォルダの中の **`start.bat`** をダブルクリックするだけ。

- 初回は必要な準備（パッケージ導入＋AIエンジンの自動DL）を行います（数分かかります）
- 2回目以降は、ダブルクリックですぐ起動します
- 起動すると、ブラウザで http://127.0.0.1:8520 が自動で開きます
- 終了するときは、出てきた黒いウィンドウを閉じるだけ

> 💡 **Python だけ事前に必要です。** 入っていない場合は `start.bat` が案内を出します。
> [python.org](https://www.python.org/downloads/) からインストールする際、最初の画面で **「Add python.exe to PATH」にチェック**を入れてください。

> 🔒 通信先は GitHub（初回のエンジンDLのみ）。**画像など個人データは一切送信されません。**

---

## 🛠 手動セットアップ（`start.bat` が使えないとき・上級者向け）

<details>
<summary>クリックして展開</summary>

### 1. リポジトリの取得

```powershell
git clone https://github.com/OMO-514/image_upscaler.git
cd image_upscaler
```

> ⬇️ Gitを使わない場合は、GitHubページの「Code → Download ZIP」から取得して解凍してもOKです。

### 2. Python依存パッケージのインストール

```powershell
py -m pip install -r requirements.txt
```

### 3. AI超解像エンジンのバイナリ配置

#### 🚀 自動セットアップ（推奨）

PowerShell で以下を実行するだけで、GitHub公式リリースから両エンジンを自動DL・配置します:

```powershell
cd image_upscaler
.\setup.ps1
```

> 🔒 通信先は GitHub のみ。画像など個人データは送信されません。

実行できない場合は PowerShell の実行ポリシーを一時的に許可:
```powershell
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```

#### 🛠 手動配置（自動が失敗した場合）

GitHubの公式リリースから手動ダウンロードして `bin/` に配置します。

#### Real-ESRGAN ncnn-Vulkan

1. https://github.com/xinntao/Real-ESRGAN/releases から最新の Windows 版 ZIP をDL
   - 例: `realesrgan-ncnn-vulkan-XXXXXXXX-windows.zip`
2. 解凍して `bin\realesrgan-ncnn-vulkan\` に配置
3. 配置後の構造:
   ```
   bin\realesrgan-ncnn-vulkan\
   ├── realesrgan-ncnn-vulkan.exe
   ├── models\
   │   ├── realesrgan-x4plus.bin / .param
   │   ├── realesrgan-x4plus-anime.bin / .param
   │   └── ...
   └── *.dll
   ```

#### waifu2x ncnn-Vulkan

1. https://github.com/nihui/waifu2x-ncnn-vulkan/releases から最新の Windows 版 ZIP をDL
2. 解凍して `bin\waifu2x-ncnn-vulkan\` に配置
3. 配置後の構造:
   ```
   bin\waifu2x-ncnn-vulkan\
   ├── waifu2x-ncnn-vulkan.exe
   ├── models\
   │   ├── models-cunet\
   │   └── ...
   └── *.dll
   ```

> 💡 どちらか一方だけでも動作します（未配置のエンジンはGUIから自動的に除外されます）

</details>

## ▶️ 起動

通常は **`start.bat` をダブルクリック**するだけです（→「かんたんスタート」参照）。

コマンドから起動したい場合:

```powershell
py -m streamlit run app.py
```

どちらの場合も、ブラウザで http://127.0.0.1:8520 が自動で開きます。

## 📂 ディレクトリ構造

```
image_upscaler\
├── start.bat           # ★これをダブルクリックで起動（準備も自動）
├── app.py              # Streamlit GUI
├── upscaler.py         # エンジン呼び出しラッパ
├── requirements.txt
├── setup.ps1           # AIエンジン自動DL（start.batが内部で使用）
├── run.bat             # 旧・起動スクリプト（start.bat推奨）
├── .streamlit\
│   └── config.toml     # localhost束縛・テレメトリOFF
├── bin\                # ← ここにエンジンバイナリを配置
├── temp\               # 一時ファイル（自動削除可）
└── output\             # 高画質化結果の保存先
```

## 🎯 使い方

1. 画像をドラッグ&ドロップ
2. サイドバーでエンジン・倍率・出力形式を選択
   - **写真** → `Real-ESRGAN (photo)`
   - **イラスト/アニメ** → `Real-ESRGAN (anime)` または `waifu2x`
3. 「🚀 高画質化を実行」をクリック
4. Before / After スライダーで比較
5. ⬇️ ダウンロード

## ⚙️ オプション

- **TTAモード**: 8方向で処理して精度UP（処理時間は8倍）
- **ノイズ除去** (waifu2xのみ): -1〜3 で強度調整
- **自動削除**: temp/ の作業ファイルを処理後に削除
- **output/保存**: タイムスタンプ付きで履歴保存

## 🐛 トラブルシューティング

| 症状 | 対処 |
|---|---|
| 「エンジンバイナリが未配置」 | 上記「初回セットアップ」の手順3を実行 |
| 処理が極端に遅い | GPUが使われていない可能性。Vulkanドライバ最新化を確認 |
| ポート8520が使用中 | `.streamlit/config.toml` の `port` を変更 |
| 画像が真っ黒 | 入力がEXIF回転情報を持つ場合がある。一度 Pillow で正規化推奨 |

## 📜 ライセンス

- 本ツール: [MIT License](LICENSE)（自由に利用・改変・再配布可）
- Real-ESRGAN: BSD 3-Clause
- waifu2x-ncnn-vulkan: MIT

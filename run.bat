@echo off
chcp 65001 > nul
cd /d "%~dp0"
echo ====================================
echo  画像高画質化ツール 起動中...
echo  http://127.0.0.1:8520 で開きます
echo ====================================
py -m streamlit run app.py
pause

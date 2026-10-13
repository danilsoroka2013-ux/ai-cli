#!/data/data/com.termux/files/usr/bin/bash
# Установка ai-cli в Termux (Android)
set -e

echo "==> Обновление пакетов Termux"
pkg update -y && pkg upgrade -y

echo "==> Установка Python и git"
pkg install -y python git

echo "==> Установка ai-cli"
pip install --upgrade pip
pip install -e .

echo "==> Готово!"
echo ""
echo "Запуск:        ai-cli chat"
echo "Список:        ai-cli providers"
echo "Ключ:          ai-cli keys set <провайдер> <ключ>"
echo ""
echo "Опционально (бесплатные провайдеры без ключа):  pip install g4f"

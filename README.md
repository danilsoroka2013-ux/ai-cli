# ai-cli

Консольный AI-ассистент с инструментами: читает и изменяет файлы, выполняет команды, ходит в интернет. Работает с разными LLM-провайдерами через ваши API-ключи, либо бесплатно через G4F.

## Провайдеры

| Провайдер | Ключ | Переменная окружения |
|---|---|---|
| OpenRouter | нужен | `OPENROUTER_API_KEY` |
| Groq | нужен | `GROQ_API_KEY` |
| OpenAI | нужен | `OPENAI_API_KEY` |
| Gemini | нужен | `GEMINI_API_KEY` |
| Alibaba (Qwen) | нужен | `DASHSCOPE_API_KEY` |
| Claude | нужен (`pip install "ai-cli[claude]"`) | `ANTHROPIC_API_KEY` |
| DeepSeek | нужен | `DEEPSEEK_API_KEY` |
| Mistral | нужен | `MISTRAL_API_KEY` |
| xAI (Grok) | нужен | `XAI_API_KEY` |
| G4F | **не нужен** (бесплатно) | — |
| Ollama | не нужен (локально) | — |

## Инструменты агента

- **Файлы:** чтение, создание, перезапись, точечная правка, дописывание, удаление, переименование, перемещение, копирование, создание папок, список, glob-поиск, grep по regex, информация о файле
- **Интернет:** загрузка страниц (HTML → текст), скачивание файлов с прогресс-баром
- **ОС:** выполнение консольных команд

Опасные действия (перезапись, удаление, команды) требуют подтверждения, с diff-превью изменений. Флаг `-y` — авто-подтверждение.

## Установка

### Windows / Linux / macOS

```bash
git clone https://github.com/danilsoroka2013-ux/ai-cli.git
cd ai-cli
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/macOS
pip install -e .
```

### Termux (Android)

```bash
pkg install -y git python
git clone https://github.com/danilsoroka2013-ux/ai-cli.git
cd ai-cli
bash install-termux.sh
```

Опционально, бесплатные провайдеры без ключа: `pip install g4f`

## Использование

```bash
ai-cli keys set groq gsk_...    # сохранить API-ключ
ai-cli use groq                 # провайдер по умолчанию
ai-cli providers                # таблица провайдеров

ai-cli chat                     # интерактивный чат
ai-cli chat -p gemini -m gemini-2.0-flash
ai-cli ask "создай скрипт backup.py и протестируй его"
ai-cli ask "..." -y             # без подтверждений
```

Команды внутри чата: `help`, `clear`, `model <имя>`, `exit`.

Без ключей: `ai-cli use g4f` (после `pip install g4f`). Цепочка g4f-провайдеров настраивается переменной `G4F_PROVIDER="LLM7,Cloudflare,GLM"`.

Ключи и настройки хранятся в `~/.ai-cli/config.json`.

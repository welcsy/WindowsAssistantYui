# WindowsAssistantYui

WindowsAssistantYui is a local windows assistant Yui. Chat with Yui will change Yui's picture with her emotion. And it's a template that you can change pictures or set emotions by yourself. Right click with Yui can open chatbox or select to exit.

## Features

- Code base: PyQt5.
- OpenAI key: should be set in config.py.
- Chat: openAI chatGPT 4o, and conversation will store in conversation.txt.
- Emotion detection: openAI chatGPT 4o, and can be set in emotion.txt.
- Pictures: made by openAI DALL-E3, and store in folder pictures.
- Pictures change: It can be set in emotion.txt.
- voice: Pyttsx3.
- Right click: "chatbox" & "exit"
- Package to .exe: PyInstaller

## Quick Start
Start with Administrator:Anaconda Prompt
```
cd WindowsAssistantYui
conda create -n .venv python=3.10
conda activate .venv
pip install pyttsx3 openai PyQt5
python myDesktopAI.py
```

## Package to .exe
```
pyinstaller -F -i "pictures/Yui.ico" --name myAI --add-data "pictures;pictures" --add-data "*.txt;." --add-data "config.py;config.py" myDesktopAI.py
```

## License

Copyright (c) 2025 welcsy
Licensed under the BSD 3-Clause License. See [LICENSE](license) file for details.

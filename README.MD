# ChatGPT-From-Stream

This Project is a proof of concept of the ability to transcribe parts of twitch streams
and using AI to summarize the content.

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install the following dependencies.

```bash
pip install speechrecognition
pip install pydub
pip install openai
pip install flask
pip install beautifulsoup4
pip install selenium
```
Download ffmpeg from the following link:<br /> https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-full.7z <br />
Extract the archive and locate the file <i>ffmpeg.exe</i>  in the bin folder.<br />
Copy <i>ffmpeg.exe</i> to the project's main folder.<br />
![alt text](https://i.imgur.com/2c3sXIQ.png)

Before usage edit the openaikey.txt and add your OpenAI API key
# 🎙️ Azure TTS Studio with Emotional Intelligence

A powerful Text-to-Speech web application that uses **FREE Azure TTS** (via edge-tts) with advanced emotion support. No API keys required!

## ✨ Features

- 🆓 **100% Free** - Uses Microsoft Edge's TTS engine (no API key needed)
- 🌍 **200+ Voices** - Multiple languages, accents, and regions
- 🎭 **Emotion Support** - Express 10 different emotions through pitch, rate, and volume modulation
- 🎨 **Beautiful UI** - Modern, responsive web interface
- 🎵 **Instant Playback** - Generate and play audio immediately
- 💾 **Download Option** - Save generated audio as MP3

## 🎭 Supported Emotions

Tag emotions in your text using square brackets:

- `[happy]` - Joyful, upbeat tone
- `[excited]` - High energy, enthusiastic
- `[sad]` - Melancholic, slower pace
- `[angry]` - Intense, forceful
- `[calm]` - Peaceful, relaxed
- `[whisper]` - Soft, quiet
- `[surprised]` - Shocked, high pitch
- `[fearful]` - Anxious, rapid
- `[disgusted]` - Disapproving tone
- `[neutral]` - Default, natural

## 📝 Example Usage

```
[happy] Hello! Welcome to the Azure TTS Studio! 
[excited] This is absolutely amazing! 
[calm] You can express emotions naturally in your speech. 
[sad] Sometimes things don't go as planned. 
[surprised] But suddenly, everything changed!
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the Application

```bash
python app.py
```

### 3. Open in Browser

Navigate to: `http://localhost:5000`

## 📦 Requirements

- Python 3.7+
- Flask 3.0.0
- edge-tts 6.1.9

## 🎯 How It Works

1. **Select Language/Region** - Choose from 200+ voices worldwide
2. **Select Voice** - Pick your preferred accent and gender
3. **Enter Text** - Type your message with emotion tags
4. **Generate** - Click the button to create your speech
5. **Listen** - Audio plays automatically and can be downloaded

## 🔧 Technical Details

### Emotion Implementation

Emotions are achieved through SSML (Speech Synthesis Markup Language) by modifying:
- **Pitch** - Voice frequency (higher for happy/excited, lower for sad)
- **Rate** - Speaking speed (faster for excited, slower for sad)
- **Volume** - Audio loudness (louder for angry, softer for whisper)

### Architecture

- **Backend**: Flask web server with async edge-tts integration
- **Frontend**: Vanilla JavaScript with responsive CSS
- **Audio**: MP3 format, generated on-the-fly

## 🌐 Available Languages

The system supports **ALL** languages available in Microsoft Edge TTS, including:
- English (US, UK, Australia, India, etc.)
- Spanish (Spain, Mexico, Argentina, etc.)
- French (France, Canada, etc.)
- German, Italian, Portuguese, Russian, Chinese, Japanese, Korean
- And 50+ more languages!

## 💡 Tips

- Use **Ctrl+Enter** in the text area to quickly generate speech
- Combine multiple emotions in one text for dynamic expression
- Experiment with different voices for various emotional effects
- Neural voices (ending in "Neural") provide the best quality

## 🔒 Privacy

- No API keys required
- No data is stored or logged
- Audio files are temporary and automatically cleaned
- All processing happens locally on your machine

## 🎓 Advanced Usage

### Custom Emotion Tags

You can modify `EMOTION_PROSODY` in `app.py` to create custom emotions:

```python
EMOTION_PROSODY = {
    'custom': {'pitch': '+15%', 'rate': '+5%', 'volume': '+8dB'},
}
```

### SSML Direct Access

The system generates SSML internally. For advanced users, you can modify the `create_ssml()` function to add additional SSML features like:
- Emphasis
- Breaks/pauses
- Say-as (numbers, dates, etc.)

## 🐛 Troubleshooting

**Issue**: Voices not loading
- **Solution**: Check internet connection (edge-tts needs to fetch voice list)

**Issue**: Audio not playing
- **Solution**: Try a different browser or check browser audio permissions

**Issue**: Slow generation
- **Solution**: Normal for first request; subsequent requests are faster

## 📄 License

MIT License - Free to use, modify, and distribute

## 🙏 Credits

- Microsoft Edge TTS for free voice synthesis
- edge-tts Python library by [@rany2](https://github.com/rany2/edge-tts)

---

**Made with ❤️ for expressive Text-to-Speech**

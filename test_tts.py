import asyncio
import edge_tts

async def test_tts():
    """Test basic edge-tts functionality"""
    text = "[happy] Hello! This is a test."
    voice = "en-US-AriaNeural"
    
    # Test with SSML
    ssml = '''<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang="en-US">
    <voice name="en-US-AriaNeural">
    <prosody pitch="+20%" rate="+10%" volume="+5dB">Hello! This is a test.</prosody>
    </voice>
    </speak>'''
    
    print("Testing SSML generation...")
    print(ssml)
    
    try:
        communicate = edge_tts.Communicate(ssml, voice)
        await communicate.save("test_output.mp3")
        print("✓ Success! Audio saved to test_output.mp3")
    except Exception as e:
        print(f"✗ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_tts())

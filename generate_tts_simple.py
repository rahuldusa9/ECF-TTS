"""
Simple wrapper script to generate TTS using edge-tts
Usage: python generate_tts_simple.py <output_file> <voice> <text> [rate] [pitch]
"""
import sys
import asyncio
import edge_tts

async def generate(output_file, voice, text, rate="+0%", pitch="+0Hz"):
    # Always generate as MP3 for consistency
    communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
    await communicate.save(output_file)
    print(f"SUCCESS: {output_file}")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("ERROR: Missing arguments")
        sys.exit(1)
    
    output_file = sys.argv[1]
    voice = sys.argv[2]
    text = sys.argv[3]
    rate = sys.argv[4] if len(sys.argv) > 4 else "+0%"
    pitch = sys.argv[5] if len(sys.argv) > 5 else "+0Hz"
    
    # Convert pitch percentage to Hz format that edge-tts expects
    # edge-tts pitch format: +50Hz, -50Hz (not percentages)
    if '%' in pitch:
        # Convert percentage to Hz (more conservative: 1% ≈ 1Hz)
        try:
            percent = int(pitch.replace('%', '').replace('+', '').replace('-', ''))
            sign = '-' if '-' in pitch else '+'
            hz_value = int(percent * 1.0)  # 1% = 1Hz for more natural sound
            pitch = f"{sign}{hz_value}Hz"
        except:
            pitch = "+0Hz"
    
    asyncio.run(generate(output_file, voice, text, rate, pitch))

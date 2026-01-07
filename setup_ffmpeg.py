"""
Download and setup ffmpeg for Windows
"""
import os
import sys
import urllib.request
import zipfile
import shutil

def download_ffmpeg():
    """Download ffmpeg essentials for Windows"""
    ffmpeg_url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    
    # Download to temp
    temp_dir = os.path.join(os.path.dirname(__file__), 'ffmpeg_temp')
    os.makedirs(temp_dir, exist_ok=True)
    
    zip_path = os.path.join(temp_dir, 'ffmpeg.zip')
    
    print("Downloading ffmpeg...")
    urllib.request.urlretrieve(ffmpeg_url, zip_path)
    
    print("Extracting...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)
    
    # Find ffmpeg.exe
    for root, dirs, files in os.walk(temp_dir):
        if 'ffmpeg.exe' in files:
            ffmpeg_exe = os.path.join(root, 'ffmpeg.exe')
            target = os.path.join(os.path.dirname(__file__), 'ffmpeg.exe')
            shutil.copy(ffmpeg_exe, target)
            print(f"Installed ffmpeg to: {target}")
            break
    
    # Cleanup
    shutil.rmtree(temp_dir)
    print("Done!")

if __name__ == "__main__":
    download_ffmpeg()

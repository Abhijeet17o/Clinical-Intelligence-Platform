"""
Script to download and install ffmpeg for Windows
"""
import os
import sys
import urllib.request
import zipfile
import shutil

def download_ffmpeg():
    """Download ffmpeg for Windows"""
    
    print("🎬 FFmpeg Installation Script")
    print("=" * 60)
    
    # FFmpeg download URL for Windows (essentials build)
    ffmpeg_url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    download_path = "ffmpeg.zip"
    extract_path = "ffmpeg_temp"
    final_path = "ffmpeg"
    
    try:
        # Check if ffmpeg already exists
        ffmpeg_exe = os.path.join(final_path, "bin", "ffmpeg.exe")
        if os.path.exists(ffmpeg_exe):
            print(f"\n✅ FFmpeg already installed at: {os.path.abspath(ffmpeg_exe)}")
            return True
        
        print(f"\n📥 Downloading ffmpeg from {ffmpeg_url}")
        print("⏳ This may take a few minutes (file size ~70MB)...")
        
        # Download with progress
        def show_progress(block_num, block_size, total_size):
            downloaded = block_num * block_size
            percent = min(downloaded * 100 / total_size, 100)
            sys.stdout.write(f"\r   Progress: {percent:.1f}%")
            sys.stdout.flush()
        
        urllib.request.urlretrieve(ffmpeg_url, download_path, show_progress)
        print("\n✅ Download complete!")
        
        # Extract
        print(f"\n📦 Extracting ffmpeg...")
        with zipfile.ZipFile(download_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
        
        # Find the extracted folder (it has a version number in the name)
        extracted_folders = os.listdir(extract_path)
        if not extracted_folders:
            raise Exception("Failed to extract ffmpeg")
        
        source_folder = os.path.join(extract_path, extracted_folders[0])
        
        # Move to final location
        if os.path.exists(final_path):
            shutil.rmtree(final_path)
        shutil.move(source_folder, final_path)
        
        # Cleanup
        os.remove(download_path)
        shutil.rmtree(extract_path)
        
        print(f"✅ FFmpeg installed successfully!")
        print(f"\n📍 Installation location: {os.path.abspath(ffmpeg_exe)}")
        
        # Add to PATH for this session
        bin_path = os.path.abspath(os.path.join(final_path, "bin"))
        os.environ['PATH'] = bin_path + os.pathsep + os.environ['PATH']
        
        print(f"\n⚠️  IMPORTANT: FFmpeg has been added to PATH for this session.")
        print(f"   To make it permanent, add this folder to your system PATH:")
        print(f"   {bin_path}")
        print(f"\n   OR simply run the app with:")
        print(f"   set PATH={bin_path};%PATH% && python app.py --no-reload")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error installing ffmpeg: {e}")
        print("\n💡 Manual Installation Steps:")
        print("1. Download ffmpeg from: https://www.gyan.dev/ffmpeg/builds/")
        print("2. Extract the zip file")
        print("3. Copy the 'bin' folder to your project directory")
        print("4. Add the bin folder to your PATH")
        return False

if __name__ == "__main__":
    success = download_ffmpeg()
    
    if success:
        print("\n" + "=" * 60)
        print("✅ Setup complete! You can now run:")
        print("   python app.py --no-reload")
        print("=" * 60)
    else:
        sys.exit(1)

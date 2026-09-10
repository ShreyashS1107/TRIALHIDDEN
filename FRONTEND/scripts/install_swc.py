import urllib.request
import tarfile
import os
import io
import shutil
import sys

def download_and_extract(url, target_dir):
    print(f"Downloading {url}...", flush=True)
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    
    buf = io.BytesIO()
    with urllib.request.urlopen(req, timeout=30) as response:
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        block_size = 1024 * 1024 # 1MB
        while True:
            chunk = response.read(block_size)
            if not chunk:
                break
            buf.write(chunk)
            downloaded += len(chunk)
            pct = (downloaded / total_size * 100) if total_size > 0 else 0
            sys.stdout.write(f"\rDownloaded {downloaded // (1024*1024)}MB / {total_size // (1024*1024)}MB ({pct:.1f}%)")
            sys.stdout.flush()
    print("\nDownload complete! Extracting...", flush=True)
    
    buf.seek(0)
    os.makedirs(target_dir, exist_ok=True)
    with tarfile.open(fileobj=buf, mode="r:gz") as tar:
        for member in tar.getmembers():
            if member.name.startswith("package/"):
                rel_path = member.name[len("package/"):]
            elif member.name.startswith("package"):
                continue
            else:
                rel_path = member.name
            
            if not rel_path:
                continue
            
            dest_path = os.path.join(target_dir, rel_path)
            if member.isdir():
                os.makedirs(dest_path, exist_ok=True)
            else:
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                with tar.extractfile(member) as src, open(dest_path, "wb") as dst:
                    shutil.copyfileobj(src, dst)
    print(f"Extraction to {target_dir} finished!\n", flush=True)

if __name__ == "__main__":
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    next_dir = os.path.join(base, "node_modules", "@next")
    
    # 1. SWC Win32 x64 MSVC
    msvc_dir = os.path.join(next_dir, "swc-win32-x64-msvc")
    download_and_extract("https://registry.npmjs.org/@next/swc-win32-x64-msvc/-/swc-win32-x64-msvc-14.2.15.tgz", msvc_dir)
    
    # 2. SWC WASM
    wasm_dir = os.path.join(next_dir, "swc-wasm-nodejs")
    download_and_extract("https://registry.npmjs.org/@next/swc-wasm-nodejs/-/swc-wasm-nodejs-14.2.15.tgz", wasm_dir)
    
    print("All SWC packages ready!", flush=True)

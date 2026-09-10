import urllib.request
import concurrent.futures
import os
import tarfile
import sys
import time

URL = "https://cdn.npmmirror.com/packages/%40next/swc-win32-x64-msvc/14.2.15/swc-win32-x64-msvc-14.2.15.tgz"
OUTPUT_TAR = "swc.tgz"
NUM_THREADS = 12

def get_content_length(url):
    req = urllib.request.Request(url, method='HEAD')
    with urllib.request.urlopen(req, timeout=15) as res:
        return int(res.headers['Content-Length'])

def download_chunk(url, start, end, chunk_idx):
    headers = {'Range': f'bytes={start}-{end}', 'User-Agent': 'Mozilla/5.0'}
    req = urllib.request.Request(url, headers=headers)
    chunk_file = f"chunk_{chunk_idx}.tmp"
    target_bytes = end - start + 1
    
    # Check if already partially or fully downloaded
    downloaded = 0
    if os.path.exists(chunk_file):
        downloaded = os.path.getsize(chunk_file)
        if downloaded == target_bytes:
            print(f"[Chunk {chunk_idx}] Already complete ({downloaded:,} bytes).")
            return chunk_idx, chunk_file
            
    with urllib.request.urlopen(req, timeout=60) as res:
        with open(chunk_file, 'wb') as f:
            while True:
                buf = res.read(65536)
                if not buf:
                    break
                f.write(buf)
                downloaded += len(buf)
                
    print(f"[Chunk {chunk_idx}] Finished ({downloaded:,} bytes).")
    return chunk_idx, chunk_file

def main():
    print(f"Connecting to {URL}...")
    total_len = get_content_length(URL)
    print(f"Total size: {total_len:,} bytes ({total_len / (1024*1024):.2f} MB)")
    
    chunk_size = total_len // NUM_THREADS
    ranges = []
    for i in range(NUM_THREADS):
        start = i * chunk_size
        end = (start + chunk_size - 1) if i < NUM_THREADS - 1 else (total_len - 1)
        ranges.append((start, end, i))
    
    start_time = time.time()
    print(f"Spawning {NUM_THREADS} threads...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
        futures = [executor.submit(download_chunk, URL, start, end, i) for start, end, i in ranges]
        for f in concurrent.futures.as_completed(futures):
            idx, cfile = f.result()
            print(f"Progress: Chunk {idx} ready.")
            
    elapsed = time.time() - start_time
    print(f"All chunks downloaded in {elapsed:.1f} seconds! Combining into {OUTPUT_TAR}...")
    with open(OUTPUT_TAR, 'wb') as out_f:
        for i in range(NUM_THREADS):
            cfile = f"chunk_{i}.tmp"
            with open(cfile, 'rb') as in_f:
                out_f.write(in_f.read())
            try:
                os.remove(cfile)
            except Exception:
                pass
            
    print(f"Successfully assembled {OUTPUT_TAR} ({os.path.getsize(OUTPUT_TAR):,} bytes).")
    
    # Extract to node_modules/@next/swc-win32-x64-msvc
    target_dir = os.path.join("node_modules", "@next", "swc-win32-x64-msvc")
    fallback_dir = os.path.join("node_modules", "next", "next-swc-fallback", "@next", "swc-win32-x64-msvc")
    os.makedirs(target_dir, exist_ok=True)
    os.makedirs(fallback_dir, exist_ok=True)
    
    print("Extracting tarball contents...")
    with tarfile.open(OUTPUT_TAR, 'r:gz') as tar:
        for member in tar.getmembers():
            filename = os.path.basename(member.name)
            if filename:
                member.name = filename
                tar.extract(member, path=target_dir)
                tar.extract(member, path=fallback_dir)
                
    node_file = os.path.join(target_dir, "next-swc.win32-x64-msvc.node")
    if os.path.exists(node_file):
        print(f"\n==========================================")
        print(f"SWC READY: {node_file}")
        print(f"Size: {os.path.getsize(node_file):,} bytes")
        print(f"==========================================\n")
    else:
        print("Extracted files in target_dir:", os.listdir(target_dir))

if __name__ == "__main__":
    main()

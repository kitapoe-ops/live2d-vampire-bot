"""
Rename all Chinese-named Live2D model files to ASCII 'vampire.*' equivalents.
Updates all internal JSON references accordingly.
Safe to re-run: skips already-renamed files.
"""
import os
import json
import shutil

# Directories to process (source + dist)
DIRS = [
    r'C:\Users\kitap\.openclaw\workspace\live2d-fork\backend\static\live2d\vampire',
    r'C:\Users\kitap\.openclaw\workspace\live2d-fork\dist-pages\live2d\vampire',
    r'C:\Users\kitap\.openclaw\workspace\live2d-fork\dist-pages\static\live2d\vampire',
]

# Rename map (old → new, relative filename)
RENAME_MAP = {
    '吸血鬼.2048':       'vampire.2048',
    '吸血鬼.cdi3.json':  'vampire.cdi3.json',
    '吸血鬼.exp3.json':  'vampire.exp3.json',
    '吸血鬼.moc3':       'vampire.moc3',
    '吸血鬼.model3.json':'vampire.model3.json',
    '吸血鬼.physics3.json': 'vampire.physics3.json',
    '吸血鬼.vtube.json': 'vampire.vtube.json',
}

# Files that reference Chinese names and need content updates
REF_FILES = [
    'vampire.model3.json',
    'items_pinned_to_model.json',
    'vampire.vtube.json',
]

def rename_and_fix(dir_path):
    """Rename files in one directory and fix internal references."""
    print(f'\n=== Processing: {dir_path} ===')
    
    # Step 1: Rename files
    for old_name, new_name in RENAME_MAP.items():
        old_path = os.path.join(dir_path, old_name)
        new_path = os.path.join(dir_path, new_name)
        
        if not os.path.exists(old_path):
            # Try already-renamed version
            if os.path.exists(new_path):
                print(f'  Already renamed: {new_name}')
            else:
                print(f'  MISSING: {old_name}')
            continue
        
        if os.path.exists(new_path):
            print(f'  Already renamed (target exists): {new_name}')
            continue
        
        # Rename directory or file
        if os.path.isdir(old_path):
            os.rename(old_path, new_path)
            print(f'  Renamed DIR: {old_name} → {new_name}')
        else:
            os.rename(old_path, new_path)
            print(f'  Renamed FILE: {old_name} → {new_name}')
    
    # Step 2: Fix JSON references in files that point to Chinese names
    content_old = '吸血鬼'
    content_new = 'vampire'
    
    for fname in REF_FILES:
        fpath = os.path.join(dir_path, fname)
        if not os.path.exists(fpath):
            continue
        
        with open(fpath, 'rb') as f:
            raw = f.read()
        
        # Only process if file contains Chinese chars
        try:
            text = raw.decode('utf-8')
        except UnicodeDecodeError:
            print(f'  SKIP (not UTF-8): {fname}')
            continue
        
        if content_old not in text:
            print(f'  No Chinese refs to fix in: {fname}')
            continue
        
        new_text = text.replace(content_old, content_new)
        
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(new_text)
        
        # Verify
        with open(fpath, 'r', encoding='utf-8') as f:
            verify = f.read()
        has_old = content_old in verify
        print(f'  Fixed: {fname} (had Chinese refs: {not has_old} cleaned)')
    
    print(f'  Done: {dir_path}')

if __name__ == '__main__':
    for d in DIRS:
        if os.path.exists(d):
            rename_and_fix(d)
        else:
            print(f'SKIP (not found): {d}')

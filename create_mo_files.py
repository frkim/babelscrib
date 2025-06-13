#!/usr/bin/env python3
"""
Create basic .mo files for Django translations
This creates minimal .mo files that Django can recognize
"""
import os
import struct

def create_mo_file(po_file_path, mo_file_path):
    """Create a basic .mo file from a .po file"""
    translations = {}
    
    # Parse .po file
    with open(po_file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    msgid = None
    msgstr = None
    in_msgid = False
    in_msgstr = False
    
    for line in lines:
        line = line.strip()
        
        if line.startswith('msgid '):
            if line == 'msgid ""':
                msgid = ""
            else:
                msgid = line[7:-1] if line.startswith('msgid "') and line.endswith('"') else None
            in_msgid = True
            in_msgstr = False
        elif line.startswith('msgstr '):
            if line == 'msgstr ""':
                msgstr = ""
            else:
                msgstr = line[8:-1] if line.startswith('msgstr "') and line.endswith('"') else None
            in_msgid = False
            in_msgstr = True
            
            # Store the translation if both msgid and msgstr are valid
            if msgid is not None and msgstr is not None and msgid != "":
                translations[msgid] = msgstr
            
        elif line.startswith('"') and line.endswith('"'):
            # Continuation line
            content = line[1:-1]  # Remove quotes
            if in_msgid and msgid is not None:
                msgid += content
            elif in_msgstr and msgstr is not None:
                msgstr += content
        elif line == "":
            # Empty line - end of entry
            if msgid is not None and msgstr is not None and msgid != "":
                translations[msgid] = msgstr
            msgid = None
            msgstr = None
            in_msgid = False
            in_msgstr = False
    
    # Handle last entry
    if msgid is not None and msgstr is not None and msgid != "":
        translations[msgid] = msgstr
    
    # Create .mo file
    create_mo_file_binary(translations, mo_file_path)
    print(f"Created {mo_file_path} with {len(translations)} translations")

def create_mo_file_binary(translations, mo_file_path):
    """Create a binary .mo file from translations dictionary"""
    
    # Add empty string as first entry (required by gettext format)
    ordered_translations = [("", "")] + list(translations.items())
    
    # Prepare data
    keys = [item[0] for item in ordered_translations]
    values = [item[1] for item in ordered_translations]
    
    # Encode strings to bytes using UTF-8
    keys_bytes = [key.encode('utf-8') for key in keys]
    values_bytes = [value.encode('utf-8') for value in values]
    
    # Calculate offsets
    key_offsets = []
    value_offsets = []
    
    # Header size: magic(4) + version(4) + count(4) + key_offset(4) + value_offset(4) + hash_size(4) + hash_offset(4) = 28 bytes
    # Plus 8 bytes per translation (length + offset) for keys and values
    keys_start = 28 + len(keys) * 16  # 8 bytes per key + 8 bytes per value
    values_start = keys_start + sum(len(k) for k in keys_bytes)
    
    key_offset = keys_start
    for key in keys_bytes:
        key_offsets.append((len(key), key_offset))
        key_offset += len(key)
    
    value_offset = values_start
    for value in values_bytes:
        value_offsets.append((len(value), value_offset))
        value_offset += len(value)
    
    # Write .mo file
    with open(mo_file_path, 'wb') as f:
        # Magic number (little endian)
        f.write(struct.pack('<I', 0x950412de))
        # Version
        f.write(struct.pack('<I', 0))
        # Number of strings
        f.write(struct.pack('<I', len(keys)))
        # Offset of key table
        f.write(struct.pack('<I', 28))
        # Offset of value table  
        f.write(struct.pack('<I', 28 + len(keys) * 8))
        # Hash table size (unused)
        f.write(struct.pack('<I', 0))
        # Hash table offset (unused)
        f.write(struct.pack('<I', 0))
        
        # Write key descriptors (length, offset)
        for length, offset in key_offsets:
            f.write(struct.pack('<I', length))
            f.write(struct.pack('<I', offset))
        
        # Write value descriptors (length, offset)
        for length, offset in value_offsets:
            f.write(struct.pack('<I', length))
            f.write(struct.pack('<I', offset))
        
        # Write keys
        for key in keys_bytes:
            f.write(key)
        
        # Write values
        for value in values_bytes:
            f.write(value)

if __name__ == "__main__":
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Create .mo files for French
    fr_po = os.path.join(script_dir, 'locale', 'fr', 'LC_MESSAGES', 'django.po')
    fr_mo = os.path.join(script_dir, 'locale', 'fr', 'LC_MESSAGES', 'django.mo')
    
    # Create .mo files for English
    en_po = os.path.join(script_dir, 'locale', 'en', 'LC_MESSAGES', 'django.po')
    en_mo = os.path.join(script_dir, 'locale', 'en', 'LC_MESSAGES', 'django.mo')
    
    if os.path.exists(fr_po):
        create_mo_file(fr_po, fr_mo)
    else:
        print(f"French .po file not found: {fr_po}")
    
    if os.path.exists(en_po):
        create_mo_file(en_po, en_mo)
    else:
        print(f"English .po file not found: {en_po}")
    
    print("Translation compilation completed!")

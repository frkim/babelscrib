#!/usr/bin/env python3
"""
Create minimal working .mo files for Django i18n
"""
import os
import struct

def create_minimal_mo_file(mo_file_path):
    """Create a minimal working .mo file"""
    # Minimal .mo file with just header and empty translation
    with open(mo_file_path, 'wb') as f:
        # Magic number (little endian)
        f.write(struct.pack('<I', 0x950412de))
        # Version
        f.write(struct.pack('<I', 0))
        # Number of strings (just header)
        f.write(struct.pack('<I', 1))
        # Offset of key table
        f.write(struct.pack('<I', 28))
        # Offset of value table  
        f.write(struct.pack('<I', 36))
        # Hash table size (unused)
        f.write(struct.pack('<I', 0))
        # Hash table offset (unused)
        f.write(struct.pack('<I', 0))
        
        # Key table (length=0, offset=44)
        f.write(struct.pack('<I', 0))  # length
        f.write(struct.pack('<I', 44))  # offset
        
        # Value table with header info (length=75, offset=44)
        header = "Content-Type: text/plain; charset=UTF-8\\n"
        header_bytes = header.encode('utf-8')
        f.write(struct.pack('<I', len(header_bytes)))  # length
        f.write(struct.pack('<I', 44 + 0))  # offset (after empty key)
        
        # Key data (empty string)
        # Value data (header)
        f.write(header_bytes)

if __name__ == "__main__":
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Create minimal .mo files
    fr_mo = os.path.join(script_dir, 'locale', 'fr', 'LC_MESSAGES', 'django.mo')
    en_mo = os.path.join(script_dir, 'locale', 'en', 'LC_MESSAGES', 'django.mo')
    
    create_minimal_mo_file(fr_mo)
    create_minimal_mo_file(en_mo)
    
    print("Minimal .mo files created!")
    print(f"Created: {fr_mo}")
    print(f"Created: {en_mo}")

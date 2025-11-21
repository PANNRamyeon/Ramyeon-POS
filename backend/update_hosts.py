"""
Script to update Windows hosts file with pos.panntech domain
"""
import os
import sys
import ctypes

def is_admin():
    """Check if running as administrator"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def update_hosts_file():
    """Add pos.panntech to hosts file"""
    hosts_path = r'C:\Windows\System32\drivers\etc\hosts'
    entry = '127.0.0.1    pos.panntech'
    
    # Check if running as admin
    if not is_admin():
        print('⚠️  This script requires administrator privileges.')
        print('   Please run as administrator.')
        return False
    
    try:
        # Read existing hosts file
        with open(hosts_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if entry already exists
        if 'pos.panntech' in content:
            print('✅ pos.panntech already exists in hosts file')
            return True
        
        # Add entry
        with open(hosts_path, 'a', encoding='utf-8') as f:
            f.write(f'\n{entry}\n')
        
        print('✅ Successfully added pos.panntech to hosts file')
        print(f'   Entry: {entry}')
        return True
        
    except PermissionError:
        print('❌ Permission denied. Please run as administrator.')
        return False
    except Exception as e:
        print(f'❌ Error updating hosts file: {e}')
        return False

if __name__ == '__main__':
    print('=' * 50)
    print('PANN POS System - Hosts File Updater')
    print('=' * 50)
    print()
    
    if update_hosts_file():
        print()
        print('✅ Setup complete!')
        print('   You can now access the app at: http://pos.panntech')
    else:
        print()
        print('❌ Setup failed. Please run as administrator.')
        sys.exit(1)


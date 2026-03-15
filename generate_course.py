#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate course URL list from YouTube playlist."""

import subprocess
import sys

def main():
    # Get playlist info
    print("Fetching playlist information...")
    result = subprocess.run([
        'yt-dlp', '--flat-playlist', '--get-id', '--get-title',
        'https://www.youtube.com/playlist?list=PLPW8O6W-1chwyTzI3BHwBLbGQoPFxPAPM'
    ], capture_output=True, text=True, timeout=180)

    lines = result.stdout.strip().split('\n')

    # Create output file
    with open('modern_embedded_course.txt', 'w', encoding='utf-8') as f:
        f.write('# Modern Embedded Systems Programming - Complete Course\n')
        f.write('# Total Videos: 55\n')
        f.write('# Playlist: https://www.youtube.com/playlist?list=PLPW8O6W-1chwyTzI3BHwBLbGQoPFxPAPM\n')
        f.write('#\n')

        i = 0
        count = 0
        while i < len(lines):
            if lines[i].startswith('#'):
                title = lines[i][1:].strip()
                f.write(f'# {title}\n')
                if i + 1 < len(lines):
                    vid_id = lines[i + 1].strip()
                    f.write(f'https://www.youtube.com/watch?v={vid_id}\n\n')
                    count += 1
                    i += 2
                else:
                    i += 1
            else:
                i += 1

    print(f'OK - Generated modern_embedded_course.txt with {count} videos')
    return 0

if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
临时文件清理脚本
清理项目中的所有临时文件和目录
"""

import glob
import shutil
from pathlib import Path


def cleanup_temp_files():
    """清理所有临时文件"""
    print("[*] 开始清理临时文件...")

    # 清理 tmpclaude-*-cwd 目录
    count = 0
    for tmpdir in glob.glob("tmpclaude-*-cwd"):
        try:
            if Path(tmpdir).exists():
                shutil.rmtree(tmpdir)
                count += 1
                print(f"  [+] 已删除: {tmpdir}")
        except Exception as e:
            print(f"  [-] 删除失败 {tmpdir}: {e}")

    if count == 0:
        print("  [i] 没有找到需要清理的临时文件")
    else:
        print(f"\n[OK] 清理完成！共删除 {count} 个临时目录")


if __name__ == "__main__":
    cleanup_temp_files()

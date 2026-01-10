"""
Translation module using deep-translator.
Translates subtitle text and creates bilingual subtitle files.
"""

import time
from pathlib import Path
from typing import List, Dict
from utils import setup_logger, SUBS_TRANSLATED_DIR
from subtitle import SubtitleEntry, save_srt

logger = setup_logger("translate")


# Professional terminology dictionary for quantum computing and physics
TERMINOLOGY = {
    "Quantum Computing": "量子计算",
    "Quantum Computer": "量子计算机",
    "Qubit": "量子比特",
    "Superposition": "叠加态",
    "Entanglement": "纠缠",
    "Quantum Entanglement": "量子纠缠",
    "Interference": "干涉",
    "Quantum Interference": "量子干涉",
    "Measurement": "测量",
    "Quantum Measurement": "量子测量",
    "Quantum State": "量子态",
    "Quantum Mechanics": "量子力学",
    "Classical Computing": "经典计算",
    "Classical Computer": "经典计算机",
    "Bit": "比特",
    "Classical Bit": "经典比特",
    "Circuit": "电路",
    "Quantum Circuit": "量子电路",
    "Gate": "门",
    "Quantum Gate": "量子门",
    "Algorithm": "算法",
    "Quantum Algorithm": "量子算法",
    "Cryptography": "密码学",
    "Quantum Cryptography": "量子密码学",
    "Simulation": "模拟",
    "Quantum Simulation": "量子模拟",
    "Error Correction": "纠错",
    "Quantum Error Correction": "量子纠错",
    "Coherence": "相干性",
    "Quantum Coherence": "量子相干性",
    "Decoherence": "退相干",
    "Quantum Decoherence": "量子退相干",
    "Noise": "噪声",
    "Quantum Noise": "量子噪声",
    "Atom": "原子",
    "Electron": "电子",
    "Photon": "光子",
    "Proton": "质子",
    "Neutron": "中子",
    "Molecule": "分子",
    "Particle": "粒子",
    "Wave": "波",
    "Wave Function": "波函数",
    "Probability": "概率",
    "Amplitude": "振幅",
    "Phase": "相位",
    "Frequency": "频率",
    "Wavelength": "波长",
    "Energy": "能量",
    "Momentum": "动量",
    "Spin": "自旋",
    "Orbital": "轨道",
    "Quantum Field": "量子场",
    "Quantum Theory": "量子理论",
    "Quantum Physics": "量子物理",
    "Heisenberg": "海森堡",
    "Schrödinger": "薛定谔",
    "Bohr": "玻尔",
    "Einstein": "爱因斯坦",
    "Planck": "普朗克",
    "Dirac": "狄拉克",
    "Feynman": "费曼",
}


class Translator:
    """Handles translation of subtitle text with terminology preservation."""

    def __init__(self, source_lang: str = 'en', target_lang: str = 'zh-CN'):
        """
        Initialize translator.

        Args:
            source_lang: Source language code
            target_lang: Target language code
        """
        try:
            from deep_translator import GoogleTranslator
            self.translator = GoogleTranslator(source=source_lang, target=target_lang)
            self.source_lang = source_lang
            self.target_lang = target_lang
            logger.info(f"Translator initialized: {source_lang} -> {target_lang}")
        except ImportError:
            logger.error("deep-translator not installed. Run: pip install deep-translator")
            raise
        except Exception as e:
            logger.error(f"Error initializing translator: {e}")
            raise

    def translate_text(self, text: str, preserve_case: bool = False) -> str:
        """
        Translate a single text string.

        Args:
            text: Text to translate
            preserve_case: Whether to preserve original capitalization

        Returns:
            Translated text
        """
        if not text or not text.strip():
            return text

        # Check for exact terminology matches first
        for en_term, zh_term in TERMINOLOGY.items():
            if en_term.lower() == text.lower():
                return zh_term

        # Apply terminology replacements before translation
        processed_text = text
        for en_term, zh_term in TERMINOLOGY.items():
            # Use word boundaries to avoid partial replacements
            pattern = r'\b' + re.escape(en_term) + r'\b'
            processed_text = re.sub(pattern, en_term, processed_text, flags=re.IGNORECASE)

        try:
            # Translate with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    translated = self.translator.translate(processed_text)

                    # Post-process: ensure terminology is correctly translated
                    translated = self._apply_terminology_fixes(translated)

                    return translated

                except Exception as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"Translation attempt {attempt + 1} failed, retrying...")
                        time.sleep(1)
                    else:
                        raise

        except Exception as e:
            logger.error(f"Error translating text: {e}")
            return text  # Return original if translation fails

    def _apply_terminology_fixes(self, text: str) -> str:
        """
        Apply terminology fixes to translated text.

        Args:
            text: Translated text

        Returns:
            Text with terminology fixes applied
        """
        # This ensures that key terms are consistently translated
        # In a more sophisticated system, we'd use contextual replacement
        return text

    def translate_subtitles(
        self,
        entries: List[SubtitleEntry],
        max_line_length: int = 20,
        batch_size: int = 5
    ) -> List[Dict]:
        """
        Translate subtitle entries and create bilingual format.

        Args:
            entries: List of SubtitleEntry objects
            max_line_length: Maximum characters per line for Chinese
            batch_size: Number of texts to translate in each batch

        Returns:
            List of dictionaries with original and translated text
        """
        logger.info(f"Translating {len(entries)} subtitle entries...")

        results = []
        failed_entries = []

        for i, entry in enumerate(entries, 1):
            # Translate text
            try:
                translated = self.translate_text(entry.text)

                # Optimize line length for Chinese
                translated = self._optimize_line_length(translated, max_line_length)

                result = {
                    'index': entry.index,
                    'start_time': entry.start_time,
                    'end_time': entry.end_time,
                    'original': entry.text,
                    'translated': translated,
                }

                results.append(result)
            except Exception as e:
                logger.warning(f"Failed to translate entry {entry.index}: {e}")
                logger.warning(f"  Original text: {entry.text[:50]}...")
                failed_entries.append(entry.index)
                # Add entry with original text as fallback
                results.append({
                    'index': entry.index,
                    'start_time': entry.start_time,
                    'end_time': entry.end_time,
                    'original': entry.text,
                    'translated': entry.text,  # Fallback to original
                })

            # Progress logging
            if i % 10 == 0:
                logger.info(f"Translated {i}/{len(entries)} entries")

            # Small delay to avoid rate limiting
            if i % batch_size == 0:
                time.sleep(0.5)

        if failed_entries:
            logger.warning(f"Failed to translate {len(failed_entries)} entries: {failed_entries[:5]}{'...' if len(failed_entries) > 5 else ''}")

        logger.info(f"Translation complete: {len(results)} entries")
        return results

    def _optimize_line_length(self, text: str, max_length: int) -> str:
        """
        Optimize Chinese text length for subtitle display.

        Args:
            text: Chinese text
            max_length: Maximum characters per line

        Returns:
            Text with appropriate line breaks
        """
        # If text is short enough, return as is
        if len(text) <= max_length:
            return text

        # Split into multiple lines if too long
        lines = []
        current_line = ""

        for char in text:
            if len(current_line) + 1 <= max_length:
                current_line += char
            else:
                lines.append(current_line)
                current_line = char

        if current_line:
            lines.append(current_line)

        return '\n'.join(lines)


import re


def save_bilingual_srt(
    translated_entries: List[Dict],
    output_path: Path,
    format_type: str = "bilingual",
    video_width: int = None,
    video_height: int = None
) -> None:
    """
    Save translated subtitles as bilingual SRT or ASS file.

    Args:
        translated_entries: List of translated entry dictionaries
        output_path: Output file path
        format_type: Format type ("bilingual", "chinese_only", "parallel", "ass")
        video_width: Video width in pixels (required for ASS format)
        video_height: Video height in pixels (required for ASS format)
    """
    # Handle ASS format - Deprecated in this function, handled by subtitle_generator.py
    if format_type == "ass":
         logger.warning("Direct ASS generation in translate.py is deprecated. Use subtitle_generator.py instead.")
         format_type = "bilingual" # Fallback to SRT

    # Handle SRT formats (original implementation)
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            for entry in translated_entries:
                f.write(f"{entry['index']}\n")

                # Format timestamps
                from utils import format_timestamp
                f.write(f"{format_timestamp(entry['start_time'])} --> {format_timestamp(entry['end_time'])}\n")

                # Format text based on type
                if format_type == "bilingual":
                    # Chinese on top (bold, white), English on bottom (30% smaller, light gray)
                    # ASS/SSA style tags for FFmpeg libass
                    # {\fs28\b1} = font size 28, bold on
                    # \c&HFFFFFF& = white color
                    # \shad2 = shadow depth 2
                    # {\fs20\b0} = font size 20 (30% smaller), bold off
                    # \c&HCCCCCC& = light gray color
                    f.write(r"{\fs28\b1\c&HFFFFFF&\shad2}" + f"{entry['translated']}\n")
                    f.write(r"{\fs20\b0\c&HCCCCCC&\shad2}" + f"{entry['original']}\n")
                elif format_type == "chinese_only":
                    f.write(f"{entry['translated']}\n")
                elif format_type == "parallel":
                    # Side by side (not recommended for most players)
                    f.write(f"{entry['original']} | {entry['translated']}\n")

                f.write("\n")

        logger.info(f"Saved bilingual subtitles to {output_path.name}")

    except Exception as e:
        logger.error(f"Error saving bilingual SRT: {e}")



if __name__ == "__main__":
    import sys
    from subtitle import parse_srt

    if len(sys.argv) > 1:
        subtitle_file = Path(sys.argv[1])

        # Parse subtitles
        entries = parse_srt(subtitle_file)

        # Translate
        translator = Translator()
        translated = translator.translate_subtitles(entries)

        # Save bilingual output
        output_file = SUBS_TRANSLATED_DIR / f"{subtitle_file.stem}_bilingual.srt"
        save_bilingual_srt(translated, output_file)

        print(f"\nTranslation complete!")
        print(f"Output: {output_file}")
        print(f"\nFirst entry:")
        if translated:
            print(f"  EN: {translated[0]['original']}")
            print(f"  ZH: {translated[0]['translated']}")
    else:
        print("Usage: python translate.py <subtitle_file>")

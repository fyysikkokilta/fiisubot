from enum import Enum
from typing import Optional, Union, List
from TexSoup import TexSoup
import re
import json
import os
from glob import glob
from dataclasses import dataclass, asdict
from tqdm import tqdm

from TexSoup.data import TexNamedEnv, BraceGroup, TexCmd, TexMathModeEnv, TexNode


def removeprefix(a, b):
    return a.removeprefix(b)


latex_row_to_plain = re.compile(r"^[\s&]*(.*?)\s*$", flags=re.MULTILINE)
has_2_columns = re.compile(r"^\s*[^\s]+\s*&\s*[^\s]+.*", flags=re.MULTILINE)


def latex_str_to_str(latex: str) -> str:
    if latex.startswith("%"):
        return ""

    # Handle non-breaking spaces
    latex = latex.replace("~", " ")

    # Handle common LaTeX escape sequences
    latex = latex.replace("\\&", "&")
    latex = latex.replace("\\$", "$")
    latex = latex.replace("\\%", "%")
    latex = latex.replace("\\#", "#")
    latex = latex.replace("\\_", "_")
    latex = latex.replace("\\{", "{")
    latex = latex.replace("\\}", "}")
    latex = latex.replace("\\textbackslash", "\\")

    # Handle quotes
    latex = latex.replace("``", "\u201c")  # Opening double quote
    latex = latex.replace("''", "\u201d")  # Closing double quote
    latex = latex.replace("`", "'")

    # Handle dashes
    latex = latex.replace("---", "—")  # em dash
    latex = latex.replace("--", "–")  # en dash

    if latex == "\\\\":
        return "\n"

    # Since there are no tables, use a simple regex that preserves spaces AND newlines
    # Use DOTALL flag so . matches newlines, allowing full content capture
    space_preserving_regex = re.compile(r"^(.*?)$", flags=re.DOTALL)
    match = space_preserving_regex.match(latex)
    if match is None:
        print(f"Warning: Could not parse latex string: {repr(latex)}")
        return latex  # Return as-is instead of breaking
    return match.group(1)


# TexSoup has bug that `\ something` is handled as `\something` instead of a literal space.
# handle these words as literals.
# Another option would be to preprocess the text so that `\ ` would be replaced by ` `.
HANDLE_AS_LITERAL = {"pykälä"}
IGNORE = {
    "raisebox",
    "hspace*",
    "vspace",
    "mbox",
    "hspace",
    "vspace*",
    "newline",
    "pagebreak",
    "flushright",
    "flushleft",
    "center",
    "includegraphics",
}
IGNORE_FORMATTING = {
    "oldstylenums",
    "textsc",
    "scriptsize",
    "mathbf",
    "normalsize",
    "footnotesize",
    "small",
    "large",
    "Large",
    "huge",
    "Huge",
    "tiny",
}


def get_visual_len(x: Union[TexCmd, str]) -> int:
    if isinstance(x, TexCmd):
        if x.name == "emph":
            assert len(x.contents) == 1
            return len(x.contents[0])
    elif isinstance(x, str):
        return len(x)
    raise ValueError("Unsupported type")


def clean_parameter_text(text: str) -> str:
    """Clean parameter text by removing/converting LaTeX artifacts"""
    if not text:
        return text

    # Handle remaining backslashes
    text = text.replace("\\\\", " ")  # Convert line breaks to spaces
    text = text.replace("\\", "")  # Remove remaining backslashes

    # Clean up multiple spaces
    text = " ".join(text.split())

    return text.strip()


def verse_args_to_str(
    latex_lines: List[Union[str, TexNamedEnv, TexCmd, TexMathModeEnv, BraceGroup]],
) -> str:
    # TODO: Add support for `~` non-breaking space
    out = ""
    for line in latex_lines:
        try:
            if isinstance(line, TexNamedEnv):
                if line.name == "chorus":
                    out += "NEWCHAPTER<i>"
                    out += verse_args_to_str(line.contents)
                    out += "</i>NEWCHAPTER"
                elif line.name == "tabular":  # Used for solos
                    contents = line.contents[len(line.args) :]
                    tabular_content = verse_args_to_str(contents)
                    # Process tabular content for role indicators
                    out += process_tabular_content(tabular_content)

            elif isinstance(line, str):
                out += latex_str_to_str(line)
            elif isinstance(line, TexCmd) or (
                hasattr(line, "name") and hasattr(line, "contents")
            ):
                if line.name in IGNORE_FORMATTING:
                    out += verse_args_to_str(line.contents)
                elif line.name == "srepeat":
                    out += ":,: "
                    out += verse_args_to_str(line.contents)
                    out += " :,: "
                elif line.name == "times":
                    out += "×"
                elif line.name in IGNORE:
                    continue
                elif line.name == "srepeatleft":
                    out += ":,: "
                    out += verse_args_to_str(line.contents)
                elif line.name == "ldots" or line.name == "dots":
                    out += "..."
                elif line.name == "textit":
                    out += "<i>"
                    out += verse_args_to_str(line.contents)
                    out += "</i>"
                elif line.name == "emph":
                    out += "<b>"
                    out += verse_args_to_str(line.contents)
                    out += "</b>"
                elif line.name in HANDLE_AS_LITERAL:
                    out += " " + line.name
                elif line.name == "sourcecodepro":
                    out += "<pre>"
                    out += verse_args_to_str(line.contents)
                    out += "</pre>"
                elif line.name == "cdots":
                    out += "..."
                elif line.name == "epsilon":
                    out += "ε"
                elif line.name == "alpha":
                    out += "α"
                elif line.name == "beta":
                    out += "β"
                elif line.name == "gamma":
                    out += "γ"
                elif line.name == "delta":
                    out += "δ"
                elif line.name == "pi":
                    out += "π"
                elif line.name == "sigma":
                    out += "σ"
                elif line.name == "omega":
                    out += "ω"
                elif line.name == "lambda":
                    out += "λ"
                elif line.name == "mu":
                    out += "μ"
                elif line.name == "tau":
                    out += "τ"
                elif line.name == "phi":
                    out += "φ"
                elif line.name == "theta":
                    out += "θ"
                elif line.name == "textbf":
                    out += "<b>"
                    out += verse_args_to_str(line.contents)
                    out += "</b>"
                elif line.name == "textrm":
                    # Regular text - just output contents
                    out += verse_args_to_str(line.contents)
                elif line.name == "underline":
                    out += "<u>"
                    out += verse_args_to_str(line.contents)
                    out += "</u>"
                elif line.name == "texttt":
                    out += "<tt>"
                    out += verse_args_to_str(line.contents)
                    out += "</tt>"
                elif line.name == "copyright":
                    out += "©"
                elif line.name == "trademark" or line.name == "texttrademark":
                    out += "™"
                elif line.name == "registered":
                    out += "®"
                elif line.name == "degree":
                    out += "°"
                elif line.name == "euro":
                    out += "€"
                elif line.name == "pounds":
                    out += "£"
                elif line.name == "yen":
                    out += "¥"
                elif line.name == "S":
                    out += "§"
                elif line.name == "P":
                    out += "¶"
                elif line.name == "dag":
                    out += "†"
                elif line.name == "ddag":
                    out += "‡"
                elif line.name == "textquotedblleft":
                    out += """
                elif line.name == "textquotedblright":
                    out += """
                elif line.name == "textquoteleft":
                    out += "'"
                elif line.name == "textquoteright":
                    out += "'"
                elif line.name == "guillemotleft":
                    out += "«"
                elif line.name == "guillemotright":
                    out += "»"
                elif line.name == "aa":
                    out += "å"
                elif line.name == "AA":
                    out += "Å"
                elif line.name == "ae":
                    out += "æ"
                elif line.name == "AE":
                    out += "Æ"
                elif line.name == "oe":
                    out += "ø"
                elif line.name == "OE":
                    out += "Ø"
                elif line.name == "ss":
                    out += "ß"
                elif line.name == "l":
                    out += "ł"
                elif line.name == "L":
                    out += "Ł"
                elif line.name == "o":
                    out += "ō"
                elif line.name == "textbar":
                    out += "|"
                elif line.name == "textasciitilde":
                    out += "~"
                elif line.name == "textasciicircum":
                    out += "^"
                elif line.name == "textbackslash":
                    out += "\\"
                elif line.name == "textgreater":
                    out += ">"
                elif line.name == "textless":
                    out += "<"
                elif line.name == "textexclamdown":
                    out += "¡"
                elif line.name == "textquestiondown":
                    out += "¿"
                elif line.name == "textemdash":
                    out += "—"
                elif line.name == "textendash":
                    out += "–"
                elif line.name == "texttimes":
                    out += "×"
                elif line.name == "textdiv":
                    out += "÷"
                elif line.name == "textpm":
                    out += "±"
                elif line.name == "textminus":
                    out += "−"
                elif line.name == "textbullet":
                    out += "•"
                elif line.name == "textperiodcentered":
                    out += "·"
                elif line.name == "textellipsis":
                    out += "…"
                elif line.name == "note":
                    # Handle note commands within verses
                    note_content = verse_args_to_str(line.contents)
                    out += f" <i>{note_content}</i> "
                elif (
                    line.name == "normalsize"
                    or line.name == "footnotesize"
                    or line.name == "small"
                    or line.name == "large"
                    or line.name == "Large"
                ):
                    # Size commands - ignore and just output contents
                    out += verse_args_to_str(line.contents)
                elif line.name == "$":
                    # Math mode - just skip the content for now
                    continue
                elif line.name == "BraceGroup":
                    # Handle unexpected BraceGroup as TexCmd
                    out += verse_args_to_str(line.contents)
                elif line.name == "normalfont":
                    # Normal font - just output contents
                    out += verse_args_to_str(line.contents)
                else:
                    # Instead of raising an exception, log a warning and skip
                    print(f"Warning: Unexpected TexCmd {line.name}, skipping")
                    continue
            elif isinstance(line, TexMathModeEnv):
                out += verse_args_to_str(line.contents)
            elif isinstance(line, BraceGroup):
                out += verse_args_to_str(line.contents)
            else:
                # Instead of raising an exception, log a warning and skip
                print(f"Warning: Unexpected line type {type(line)}, skipping")
                continue
        except Exception as e:
            print(f"Error processing line {line}: {e}")
            continue
    return out


def process_tabular_content(content: str) -> str:
    """Process tabular content to format role indicators properly"""
    import re

    # Pattern to match role indicators at the start of lines
    role_pattern = r"^(\s*)(soolo|kaikki|kuoro|joku™?):(\s*)"

    # Split content into lines and process each line
    lines = content.split("\n")
    processed_lines = []

    for line in lines:
        # Check if line starts with a role indicator
        match = re.match(role_pattern, line, re.IGNORECASE)
        if match:
            prefix = match.group(1)  # whitespace before
            role = match.group(2)  # the role (soolo, kaikki, etc.)
            suffix = match.group(3)  # whitespace after
            rest = line[match.end() :]  # rest of the line

            # Format the role indicator
            formatted_line = f"{prefix}<b>{role}:</b>{suffix}{rest}"
            processed_lines.append(formatted_line)
        else:
            processed_lines.append(line)

    return "\n".join(processed_lines)


def handle_uverse(uverse: TexSoup) -> str:
    import re

    assert len(uverse.args) == 1
    assert isinstance(uverse.args[0], BraceGroup)

    # Get the raw verse content
    raw_content = verse_args_to_str(uverse.args[0].contents)

    # Clean up whitespace specifically for verse content
    # 1. Replace multiple newlines with single newlines
    cleaned = re.sub(r"\n\s*\n+", "\n", raw_content)

    # 2. Remove leading/trailing whitespace from each line and clean up multiple spaces
    lines = cleaned.split("\n")
    cleaned_lines = []
    for line in lines:
        # Strip leading/trailing whitespace
        line = line.strip()
        if line:
            # Replace multiple consecutive spaces with single spaces
            line = re.sub(r"\s+", " ", line)
            cleaned_lines.append(line)

    # 3. Join with single newlines
    return "\n".join(cleaned_lines)


def handle_nverse(nverse: TexSoup) -> str:
    """Handle numbered verses (nverse and mnverse) similar to uverse"""
    import re

    # For nverse, there's one argument (the verse content)
    if len(nverse.args) == 1:
        assert isinstance(nverse.args[0], BraceGroup)
        raw_content = verse_args_to_str(nverse.args[0].contents)
    # For mnverse, there are two arguments (verse content and repeat content)
    elif len(nverse.args) == 2:
        assert isinstance(nverse.args[0], BraceGroup)
        assert isinstance(nverse.args[1], BraceGroup)
        verse_content = verse_args_to_str(nverse.args[0].contents)
        repeat_content = verse_args_to_str(nverse.args[1].contents)
        raw_content = verse_content + "\n" + repeat_content
    else:
        print(f"Warning: Unexpected number of arguments for {nverse.name}")
        return ""

    # Clean up whitespace specifically for verse content
    # 1. Replace multiple newlines with single newlines
    cleaned = re.sub(r"\n\s*\n+", "\n", raw_content)

    # 2. Remove leading/trailing whitespace from each line and clean up multiple spaces
    lines = cleaned.split("\n")
    cleaned_lines = []
    for line in lines:
        # Strip leading/trailing whitespace
        line = line.strip()
        if line:
            # Replace multiple consecutive spaces with single spaces
            line = re.sub(r"\s+", " ", line)
            cleaned_lines.append(line)

    # 3. Join with single newlines
    return "\n".join(cleaned_lines)


class VerseType(str, Enum):
    unnumbered = "uverse"
    numbered = "nverse"
    twice_numbered = "mnverse"
    subsong = "subsong"


SKIP_VERSE_TYPES = {
    "raisebox",
    "scriptsize",
    "wrapfigure",
    "trad.",
    "pagebreak",
    "newline",
    "BraceGroup",
    "vspace*",
    "vspace",
    "hspace",
    "hspace*",
    "includegraphics",
    "figure",
    "center",
    "flushright",
    "flushleft",
    "raggedright",
    "raggedleft",
    "note",  # notes are handled separately
}


def handle_verses_no_subsongs(content: List[TexNode]) -> str:
    """Handle verses but skip subsongs (they will be processed separately)"""
    out = ""
    for c in content:
        try:
            if not hasattr(c, "name") or c.name in SKIP_VERSE_TYPES:
                continue

            if not isinstance(c, TexNode):
                continue

            if c.name == "samepage":
                out += handle_verses_no_subsongs(c.contents)
            elif c.name == "uverse":
                out += "NEWCHAPTER"
                out += handle_uverse(c)
                out += "NEWCHAPTER"
            elif c.name == "nverse" or c.name == "mnverse":
                out += "NEWCHAPTER"
                out += handle_nverse(c)
                out += "NEWCHAPTER"
            elif c.name == "chorus":
                out += "NEWCHAPTER<i>"
                out += verse_args_to_str(c.contents)
                out += "</i>NEWCHAPTER"
            elif c.name == "subsong":
                # Skip subsongs - they will be processed separately
                continue
            elif c.name == "note":
                # Handle note commands
                note_content = verse_args_to_str(c.contents)
                out += f"NEWCHAPTER<i>{note_content}</i>NEWCHAPTER"
            else:
                print(f"Warning: Unexpected verse type `{c.name}`, skipping")
                continue
        except Exception as e:
            print(f"Error processing verse content {c}: {e}")
            continue

    # Clean up the final output to ensure consistent spacing
    return clean_final_output(out)


def clean_final_output(text: str) -> str:
    """Clean up the final output to ensure consistent spacing"""
    import re

    # Replace NEWCHAPTER placeholders with two newlines
    text = text.replace("NEWCHAPTER", "\n\n")

    # Remove leading/trailing whitespace
    text = text.strip()

    # Replace multiple consecutive newlines with exactly two newlines
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Ensure the text ends with exactly two newlines
    if text and not text.endswith("\n\n"):
        text += "\n\n"

    return text


def extract_subsongs(content: List[TexNode]) -> List[tuple]:
    """Extract subsongs as separate entities"""
    subsongs = []

    def _extract_from_content(nodes):
        for c in nodes:
            try:
                if not hasattr(c, "name"):
                    continue

                if not isinstance(c, TexNode):
                    continue

                if c.name == "samepage":
                    _extract_from_content(c.contents)
                elif c.name == "subsong":
                    # Extract subsong name from first argument with proper LaTeX processing
                    subsong_name = "Subsong"
                    if (
                        c.args
                        and len(c.args) > 0
                        and hasattr(c.args[0], "contents")
                        and c.args[0].contents
                    ):
                        subsong_name = clean_parameter_text(
                            verse_args_to_str(c.args[0].contents)
                        )

                    # Extract optional melody from second argument with proper LaTeX processing
                    subsong_melody = None
                    if (
                        c.args
                        and len(c.args) > 1
                        and hasattr(c.args[1], "contents")
                        and c.args[1].contents
                    ):
                        melody_content = clean_parameter_text(
                            verse_args_to_str(c.args[1].contents)
                        )
                        if melody_content:  # Only set if not empty
                            subsong_melody = melody_content

                    # Process subsong contents (verses, chorus, etc.)
                    subsong_lyrics = handle_verses_no_subsongs(c.contents)

                    subsongs.append((subsong_name, subsong_melody, subsong_lyrics))
            except Exception as e:
                print(f"Error processing subsong {c}: {e}")
                continue

    _extract_from_content(content)
    return subsongs


def extract_notes(content: List[TexNode]) -> List[str]:
    """Extract notes from document content"""
    notes = []

    def _extract_notes_from_content(nodes):
        for c in nodes:
            try:
                if not hasattr(c, "name"):
                    continue

                if not isinstance(c, TexNode):
                    continue

                if c.name == "note":
                    note_content = verse_args_to_str(c.contents)
                    notes.append(note_content)
                # Don't recursively search inside song environments or other complex structures
                # as this can cause infinite loops and content duplication
                elif c.name in ["samepage", "subsong"]:
                    _extract_notes_from_content(c.contents)
            except Exception as e:
                print(f"Error processing note {c}: {e}")
                continue

    _extract_notes_from_content(content)
    return notes


@dataclass
class SongInfo:
    name: str
    melody: Optional[str]
    composer: Optional[str]
    arranger: Optional[str]
    lyrics: str
    # Additional original song information
    notes: Optional[str] = None


first_or_none = lambda x: x[0] if x else None


def parse_tex(content: Union[str, bytes]) -> List[SongInfo]:
    try:
        t: TexNode = TexSoup(content)
        nones = [None] * 10
        song = t.song or t.hymnisong

        if not song:
            raise ValueError("No song or hymnisong environment found")

        name, melody, _, _, _, composer, arranger, *_ = song.args + nones
        song_content = song.children

        # Safely extract name with proper LaTeX processing
        song_name = "Unknown Song"
        if name and hasattr(name, "contents") and name.contents:
            song_name = clean_parameter_text(verse_args_to_str(name.contents))

        # Safely extract melody with proper LaTeX processing
        song_melody = None
        if melody and hasattr(melody, "contents") and melody.contents:
            melody_processed = clean_parameter_text(verse_args_to_str(melody.contents))
            if melody_processed:  # Only set if not empty after processing
                song_melody = melody_processed

        # Safely extract composer with proper LaTeX processing
        song_composer = None
        if composer and hasattr(composer, "contents") and composer.contents:
            composer_processed = clean_parameter_text(
                verse_args_to_str(composer.contents)
            )
            if composer_processed:  # Only set if not empty after processing
                song_composer = composer_processed

        # Safely extract arranger with proper LaTeX processing
        song_arranger = None
        if arranger and hasattr(arranger, "contents") and arranger.contents:
            arranger_processed = clean_parameter_text(
                verse_args_to_str(arranger.contents)
            )
            if arranger_processed:  # Only set if not empty after processing
                song_arranger = arranger_processed

        # Extract notes from the entire document (notes are typically after the song environment)
        song_notes_list = extract_notes(t.contents)
        song_notes = " | ".join(song_notes_list) if song_notes_list else None

        # Extract subsongs
        subsongs = extract_subsongs(song_content)

        # Get main song lyrics (without subsongs)
        main_lyrics = handle_verses_no_subsongs(song_content).strip()

        songs = []

        # If there are subsongs, create separate songs for each
        if subsongs:
            for subsong_name, subsong_melody, subsong_lyrics in subsongs:
                # Create a combined name for the subsong
                full_subsong_name = f"{song_name} - {subsong_name}"

                songs.append(
                    SongInfo(
                        name=full_subsong_name,
                        melody=subsong_melody
                        or song_melody,  # Use subsong melody if available, fallback to original melody
                        composer=song_composer,
                        arranger=song_arranger,
                        lyrics=subsong_lyrics.strip(),
                        notes=song_notes,
                    )
                )

        # If there's main content (verses outside of subsongs), add it as the main song
        if main_lyrics:
            songs.insert(
                0,
                SongInfo(
                    name=song_name,
                    melody=song_melody,
                    composer=song_composer,
                    arranger=song_arranger,
                    lyrics=main_lyrics,
                    notes=song_notes,
                ),
            )

        # If no subsongs and no main content, return the original single song
        if not songs:
            songs.append(
                SongInfo(
                    name=song_name,
                    melody=song_melody,
                    composer=song_composer,
                    arranger=song_arranger,
                    lyrics="No content found",
                    notes=song_notes,
                )
            )

        return songs

    except Exception as e:
        print(f"Error parsing TeX content: {e}")
        # Return a minimal song info
        return [
            SongInfo(
                name="Parse Error",
                melody=None,
                composer=None,
                arranger=None,
                lyrics="Could not parse this song",
            )
        ]


# WHITELIST = ("eino", "")
WHITELIST = ("",)


def song_contains_todo(song: SongInfo) -> bool:
    """Check if a song contains 'TODO' in any of its fields."""
    fields_to_check = [
        song.name,
        song.melody,
        song.composer,
        song.arranger,
        song.lyrics,
        song.notes,
    ]

    for field in fields_to_check:
        if field and "TODO" in field:
            return True

    return False


def main():
    songs = []
    failed_files = []

    print("Starting song extraction from Fiisut-V/songs/*.tex")
    tex_files = glob("Fiisut-V/songs/*.tex")
    print(f"Found {len(tex_files)} .tex files")

    for pa in tqdm(tex_files, desc="Processing songs"):
        if not any(x in pa.lower() for x in WHITELIST):
            continue

        try:
            # Try different encodings
            tex = None
            for encoding in ["utf-8", "latin-1", "cp1252"]:
                try:
                    with open(pa, encoding=encoding) as f:
                        tex = f.read()
                    break
                except UnicodeDecodeError:
                    continue

            if tex is None:
                print(f"Could not decode file {pa} with any encoding")
                failed_files.append(pa)
                continue

            parsed_songs = parse_tex(tex)

            # Process each song (main song and subsongs)
            for song in parsed_songs:
                if song.name != "Parse Error":
                    # Filter out songs that contain TODO in any field
                    if not song_contains_todo(song):
                        songs.append(asdict(song))
                else:
                    failed_files.append(pa)
                    break  # If any song failed, mark the whole file as failed

        except Exception as e:
            print(f"Error processing file {pa}: {e}")
            failed_files.append(pa)
            continue

    print(f"\nSuccessfully processed {len(songs)} songs")
    if failed_files:
        print(f"Failed to process {len(failed_files)} files:")
        for f in failed_files:
            print(f"  - {f}")

    # Write with proper UTF-8 encoding
    with open("songs.json", "w", encoding="utf-8") as f:
        json.dump(songs, f, indent=2, ensure_ascii=False)

    print(f"Wrote {len(songs)} songs to songs.json")


if __name__ == "__main__":
    main()

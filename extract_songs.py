from enum import Enum
from typing import Optional, Union, List
from TexSoup import TexSoup
import re

from TexSoup.data import TexNamedEnv, BraceGroup, TexCmd, TexMathModeEnv, TexNode
import sys

if sys.version_info >= (3, 9):

    def removeprefix(a, b):
        return a.removeprefix(b)

else:

    def removeprefix(a, b):
        return a[len(b) :] if a.startswith(b) else a


latex_row_to_plain = re.compile(r"^[\s&]*(.*?)\s*$", flags=re.MULTILINE)
has_2_columns = re.compile(r"^\s*[^\s]+\s*&\s*[^\s]+.*", flags=re.MULTILINE)


def latex_str_to_str(latex: str) -> str:
    if latex.startswith("%"):
        return ""

    # latex = removeprefix(latex, "\n")  # This maybe shouldn't in this function
    # latex = latex.replace("\\\\", "\n")

    # if '\\\\' in latex and latex != '\\\\':
    #     print("Found double backslash")
    #     print(repr(latex))
    if latex == "\\\\":
        return "\n"
    if has_2_columns.match(latex):
        latex = latex.replace("&", "\n")
    match = latex_row_to_plain.match(latex)
    if match is None:
        print(f"Warning: Could not parse latex string: {repr(latex)}")
        return latex  # Return as-is instead of breaking
    return match.group(1)


# TexSoup has bug that `\ something` is handled as `\something` instead of a literal space.
# handle these words as literals.
# Another option would be to preprocess the text so that `\ ` would be replaced by ` `.
HANDLE_AS_LITERAL = {"pykälä"}
IGNORE = {"raisebox", "hspace*", "vspace", "mbox"}
IGNORE_FORMATTING = {"oldstylenums", "textsc", "scriptsize", "mathbf"}


def get_visual_len(x: Union[TexCmd, str]) -> int:
    if isinstance(x, TexCmd):
        if x.name == "emph":
            assert len(x.contents) == 1
            return len(x.contents[0])
    elif isinstance(x, str):
        return len(x)
    raise ValueError("Unsupported type")


def verse_args_to_str(
    latex_lines: List[Union[str, TexNamedEnv, TexCmd, TexMathModeEnv, BraceGroup]],
) -> str:
    # TODO: Add support for `~` non-breaking space
    out = ""
    for line in latex_lines:
        try:
            if isinstance(line, TexNamedEnv):
                if line.name == "chorus":
                    assert line.name == "chorus"
                    out += "<i>"
                    out += verse_args_to_str(line.contents)
                    out += "</i>"
                elif line.name == "tabular":  # Used for solos
                    contents = line.contents[len(line.args) :]
                    out += verse_args_to_str(contents)

            elif isinstance(line, str):
                out += latex_str_to_str(line)
            elif isinstance(line, TexCmd):
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


def handle_chorus(chorus: TexSoup) -> str: ...


def handle_uverse(uverse: TexSoup) -> str:
    assert len(uverse.args) == 1
    assert isinstance(uverse.args[0], BraceGroup)
    return verse_args_to_str(uverse.args[0].contents)


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
}


def handle_verses(content: List[TexNode]) -> str:
    out = ""
    for c in content:
        try:
            if not hasattr(c, "name") or c.name in SKIP_VERSE_TYPES:
                continue

            if not isinstance(c, TexNode):
                continue

            if c.name == "samepage":
                out += handle_verses(c.contents)
            elif c.name == "uverse":
                out += handle_uverse(c)
                out += "\n\n"
            elif c.name == "subsong":
                verses = [
                    a for a in c.contents if isinstance(a, TexNode)
                ]  # name str, verses uverse TexNodes
                name = c.contents[0]  # c.args[0]
                # alt_name = c.args[1].content  (BraceGroup contents)
                out += "<i>" + str(name) + "</i>\n"
                out += handle_verses(verses)
                out += "\n\n"
            else:
                print(f"Warning: Unexpected verse type `{c.name}`, skipping")
                continue
        except Exception as e:
            print(f"Error processing verse content {c}: {e}")
            continue
    return out


from dataclasses import dataclass


@dataclass
class SongInfo:
    name: str
    melody: Optional[str]
    composer: Optional[str]
    arranger: Optional[str]
    lyrics: str


first_or_none = lambda x: x[0] if x else None


def parse_tex(content: Union[str, bytes]) -> SongInfo:
    try:
        t: TexNode = TexSoup(content)
        nones = [None] * 10
        song = t.song or t.hymnisong

        if not song:
            raise ValueError("No song or hymnisong environment found")

        name, melody, _, _, start_alt_name, composer, arranger, *_ = song.args + nones
        song_content = song.children

        # Safely extract name
        song_name = "Unknown Song"
        if name and hasattr(name, "contents") and name.contents:
            song_name = str(name.contents[0]).replace("~", " ")

        # Safely extract melody
        song_melody = None
        if melody and hasattr(melody, "contents") and melody.contents:
            song_melody = str(melody.contents[0])

        # Safely extract composer
        song_composer = None
        if composer and hasattr(composer, "contents") and composer.contents:
            song_composer = str(composer.contents[0])

        # Safely extract arranger
        song_arranger = None
        if arranger and hasattr(arranger, "contents") and arranger.contents:
            song_arranger = str(arranger.contents[0])

        return SongInfo(
            name=song_name,
            melody=song_melody,
            composer=song_composer,
            arranger=song_arranger,
            lyrics=handle_verses(song_content),
        )
    except Exception as e:
        print(f"Error parsing TeX content: {e}")
        # Return a minimal song info
        return SongInfo(
            name="Parse Error",
            melody=None,
            composer=None,
            arranger=None,
            lyrics="Could not parse this song",
        )


from glob import glob
from dataclasses import asdict
import json
from tqdm import tqdm
import os

# WHITELIST = ("eino", "")
WHITELIST = ("",)


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

            song = parse_tex(tex)

            # Skip songs that failed to parse properly
            if song.name != "Parse Error":
                songs.append(asdict(song))
            else:
                failed_files.append(pa)

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

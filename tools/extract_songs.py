from enum import Enum
from TexSoup import TexSoup

from TexSoup.data import TexNamedEnv, BraceGroup, TexCmd, TexMathModeEnv, TexNode


def latex_str_to_str(latex: str) -> str:
    if latex.startswith("%"):
        return ""

    latex = latex.removeprefix("\n")  # This maybe shouldn't in this function
    latex = latex.replace("\\\\", "\n")
    return latex


# TexSoup has bug that `\ something` is handled as `\something` instead of a literal space.
# handle these words as literals.
# Another option would be to preprocess the text so that `\ ` would be replaced by ` `.
HANDLE_AS_LITERAL = {"pykälä"}
IGNORE = {"raisebox", "hspace*", "vspace", "mbox"}
IGNORE_FORMATTING = {"oldstylenums", "textsc", "scriptsize", "mathbf"}

import warnings


def verse_args_to_str(
    latex_lines: list[str | TexNamedEnv | TexCmd | TexMathModeEnv | BraceGroup],
) -> str:
    # TODO: Add support for `~` non-breaking space
    out = ""
    for line in latex_lines:
        if isinstance(line, TexNamedEnv):
            if line.name == "chorus":
                assert line.name == "chorus"
                out += "<BEGIN ITALIC>"
                out += verse_args_to_str(line.contents)
                out += "<END ITALIC>"
            elif line.name == "tabular":  # Used for solos
                contents = line.contents[len(line.args) :]
                # out += "soolo:\"
                out += verse_args_to_str(contents)
                # raise ValueError("tabular not supported")

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
                out += "<BEGIN ITALIC>"
                out += verse_args_to_str(line.contents)
                out += "<END ITALIC>"
            elif line.name == "emph":
                out += "<BEGIN BOLD>"
                out += verse_args_to_str(line.contents)
                out += "<END BOLD>"
            elif line.name in HANDLE_AS_LITERAL:
                out += " " + line.name
            elif line.name == "sourcecodepro":
                out += "```"
                out += verse_args_to_str(line.contents)
                out += "```"
            elif line.name == "cdots":
                out += "..."
            elif line.name == "epsilon":
                out += "ε"
            else:
                # print(line)
                raise ValueError(f"Unexpected TexCmd {line.name}")
        elif isinstance(line, TexMathModeEnv):
            out += verse_args_to_str(line.contents)
        elif isinstance(line, BraceGroup):
            out += verse_args_to_str(line.contents)
        else:
            # print(line)
            raise ValueError(f"Unexpected line type {type(line)}")
    return out


def handle_chorus(chorus: TexSoup) -> str:
    ...


def handle_uverse(uverse: TexSoup) -> str:
    assert len(uverse.args) == 1
    assert isinstance(uverse.args[0], BraceGroup)
    return verse_args_to_str(uverse.args[0].contents)


class VerseType(str, Enum):
    unnumbered = "uverse"
    numbered = "nverse"
    twice_numbered = "mnverse"
    subsong = 'subsong'


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




def handle_verses(content: list[TexNode]) -> str:
    out = ""
    for c in content:
        if c.name in SKIP_VERSE_TYPES:
            continue

        assert isinstance(c, TexNode)
        if c.name == 'samepage':
          out += handle_verses(c.contents)
        elif c.name == 'uverse':
          out += handle_uverse(c)
          out += "\n"
        elif c.name == 'subsong':
          verses = [a for a in c.contents if isinstance(a, TexNode)] # name str, verses uverse TexNodes
          name = c.contents[0]  # c.args[0]
          # alt_name = c.args[1].content  (BraceGroup contents)
          out += "[ITALIC]" + name + "[END ITALIC]\n"
          out += handle_verses(verses)
          out += '\n'
        else:
          raise ValueError(f'Unexpected verse type `{c.name}`')
    return out


from dataclasses import dataclass


@dataclass
class SongInfo:
    name: str
    melody: str | None
    composer: str | None
    arranger: str | None
    lyrics: str

first_or_none = lambda x: x[0] if x else None

def parse_tex(content: str | bytes) -> SongInfo:
    t: TexNode = TexSoup(content)
    nones = [None] * 10
    song = t.song or t.hymnisong
    name, melody, _, _, start_alt_name, composer, arranger, *_ = song.args + nones
    song_content = song.children
    return SongInfo(
        name=name.contents[0],
        melody=melody.contents[0] if melody and melody.contents else None,
        composer=composer.contents[0] if composer and composer.contents else None,
        arranger=arranger.contents[0] if arranger and arranger.contents else None,
        lyrics=handle_verses(song_content),
    )


from glob import glob
from dataclasses import asdict
import json

songs = {}

for pa in glob("Fiisut-V/songs/*.tex"):
    with open(pa) as f:
        tex = f.read()
    song = parse_tex(tex)
    songs[song.name] = asdict(song)

with open('songs.json', 'w') as f:
  json.dump(songs, f, indent=2)

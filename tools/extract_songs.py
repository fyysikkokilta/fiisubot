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
    #     breakpoint()
    #     print("hmm")
    if latex == "\\\\":
        return "\n"
    if has_2_columns.match(latex):
        latex = latex.replace("&", "\n")
    match = latex_row_to_plain.match(latex)
    if match is None:
        breakpoint()
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
        if isinstance(line, TexNamedEnv):
            if line.name == "chorus":
                assert line.name == "chorus"
                out += "<i>"
                out += verse_args_to_str(line.contents)
                out += "</i>"
            elif line.name == "tabular":  # Used for solos
                contents = line.contents[len(line.args) :]

                out += verse_args_to_str(contents)

                # out += "soolo:\"
                # table = AstroTable.read([str(line)], format="latex", header_start=None, data_start=0)
                # line.append('\\\\')
                # breakpoint()
                # table = AstroTable.read([str(line)], format="latex", header_start=None, data_start=0)
                # try:
                #    table = AstroTable.read([str(line)], format="latex", header_start=None, data_start=0)
                # except Exception as e:
                #    breakpoint()
                #    print(e)
                # https://stackoverflow.com/a/14529615/13994822
                # lines = [list(g) for k, g in itertools.groupby(contents, lambda x: x=='\\\\') if not k]
                # lines = [
                #     part.split('&') if isinstance(part, str) else [part]
                #     for l in lines
                #     for part in l
                # ]
                # max_side_by_side = max(len(l) for l in lines)
                # part_width = [
                #     max(get_visual_len(line[i]) if i < len(line) else 0 for line in lines)
                #     for i in range(max_side_by_side)
                # ]
                # padded_parts = [

                #     for line in lines
                #     for i in
                # ]

                # breakpoint()

                # out += verse_args_to_str(contents)
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
        if c.name in SKIP_VERSE_TYPES:
            continue

        assert isinstance(c, TexNode)
        if c.name == "samepage":
            out += handle_verses(c.contents)
        elif c.name == "uverse":
            out += handle_uverse(c)
            out += "\n"
        elif c.name == "subsong":
            verses = [
                a for a in c.contents if isinstance(a, TexNode)
            ]  # name str, verses uverse TexNodes
            name = c.contents[0]  # c.args[0]
            # alt_name = c.args[1].content  (BraceGroup contents)
            out += "<i>" + name + "</i>\n"
            out += handle_verses(verses)
            out += "\n"
        else:
            raise ValueError(f"Unexpected verse type `{c.name}`")
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
    t: TexNode = TexSoup(content)
    nones = [None] * 10
    song = t.song or t.hymnisong
    name, melody, _, _, start_alt_name, composer, arranger, *_ = song.args + nones
    song_content = song.children
    return SongInfo(
        name=name.contents[0].replace("~", " "),
        melody=melody.contents[0] if melody and melody.contents else None,
        composer=composer.contents[0] if composer and composer.contents else None,
        arranger=arranger.contents[0] if arranger and arranger.contents else None,
        lyrics=handle_verses(song_content),
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

    # os.mkdir("songs")
    for pa in tqdm(glob("Fiisut-V/songs/*.tex")):
        if not any(x in pa.lower() for x in WHITELIST):
            continue
        with open(pa) as f:
            tex = f.read()
        song = parse_tex(tex)
        songs.append(asdict(song))

        # with open(
        #     f'songs/{song.name.replace(" ", "_").replace("/", "-")}.txt', "w"
        # ) as f:
        #     f.writelines(f"{song.name}\n\n{song.lyrics}\n\n")
        # print(f"{song.name}\n\n{song.lyrics}\n\n")

    with open("songs.json", "w") as f:
        json.dump(songs, f, indent=2)


if __name__ == "__main__":
    main()

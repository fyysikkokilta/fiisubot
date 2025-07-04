#!/usr/bin/env python3
"""Integration test for TODO filtering in the main extraction process."""

import tempfile
import os
import json
from pathlib import Path

# Create a temporary directory structure to simulate Fiisut-V/songs/
def test_main_extraction_with_todo_filtering():
    """Test that the main function properly filters out songs with TODO."""
    
    # Create temporary directory structure
    with tempfile.TemporaryDirectory() as temp_dir:
        songs_dir = Path(temp_dir) / "Fiisut-V" / "songs"
        songs_dir.mkdir(parents=True)
        
        # Create a mock .tex file with a song containing TODO
        song_with_todo = songs_dir / "song_with_todo.tex"
        song_with_todo.write_text(r"""
\begin{song}{TODO: Add proper title}{Traditional}{}{}{}{}{}
\begin{uverse}
This is a test song with TODO in title
\end{uverse}
\end{song}
""")
        
        # Create a mock .tex file with a normal song
        normal_song = songs_dir / "normal_song.tex"
        normal_song.write_text(r"""
\begin{song}{Normal Song}{Traditional}{}{}{}{}{}
\begin{uverse}
This is a normal song without any issues
\end{uverse}
\end{song}
""")
        
        # Change to the temp directory and run extraction
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            
            # Import and run the main function
            import sys
            sys.path.insert(0, original_cwd)
            from extract_songs import main
            
            # Run the extraction
            main()
            
            # Check the results
            songs_file = Path(temp_dir) / "songs.json"
            if songs_file.exists():
                with open(songs_file, 'r', encoding='utf-8') as f:
                    songs = json.load(f)
                
                print(f"Total songs extracted: {len(songs)}")
                
                # Check that songs with TODO were filtered out
                song_names = [song['name'] for song in songs]
                print(f"Song names: {song_names}")
                
                # Verify no song has TODO in the name
                todo_songs = [song for song in songs if 'TODO' in song.get('name', '')]
                assert len(todo_songs) == 0, f"Found songs with TODO that should have been filtered: {todo_songs}"
                
                print("✓ TODO filtering test passed!")
            else:
                print("No songs.json file was created")
                
        finally:
            os.chdir(original_cwd)


if __name__ == "__main__":
    test_main_extraction_with_todo_filtering()
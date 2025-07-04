#!/usr/bin/env python3
"""Test TODO filtering functionality."""

import pytest
from extract_songs import SongInfo, song_contains_todo


def test_song_contains_todo_in_name():
    """Test that songs with TODO in name are detected."""
    song = SongInfo(
        name="TODO: Add lyrics",
        melody=None,
        composer=None,
        arranger=None,
        lyrics="Some lyrics",
        notes=None
    )
    assert song_contains_todo(song) is True


def test_song_contains_todo_in_lyrics():
    """Test that songs with TODO in lyrics are detected."""
    song = SongInfo(
        name="Test Song",
        melody=None,
        composer=None,
        arranger=None,
        lyrics="First verse\nTODO: Write second verse",
        notes=None
    )
    assert song_contains_todo(song) is True


def test_song_contains_todo_in_melody():
    """Test that songs with TODO in melody are detected."""
    song = SongInfo(
        name="Test Song",
        melody="TODO: Add melody",
        composer=None,
        arranger=None,
        lyrics="Some lyrics",
        notes=None
    )
    assert song_contains_todo(song) is True


def test_song_contains_todo_in_composer():
    """Test that songs with TODO in composer are detected."""
    song = SongInfo(
        name="Test Song",
        melody=None,
        composer="TODO: Find composer",
        arranger=None,
        lyrics="Some lyrics",
        notes=None
    )
    assert song_contains_todo(song) is True


def test_song_contains_todo_in_arranger():
    """Test that songs with TODO in arranger are detected."""
    song = SongInfo(
        name="Test Song",
        melody=None,
        composer=None,
        arranger="TODO: Credit arranger",
        lyrics="Some lyrics",
        notes=None
    )
    assert song_contains_todo(song) is True


def test_song_contains_todo_in_notes():
    """Test that songs with TODO in notes are detected."""
    song = SongInfo(
        name="Test Song",
        melody=None,
        composer=None,
        arranger=None,
        lyrics="Some lyrics",
        notes="TODO: Add historical context"
    )
    assert song_contains_todo(song) is True


def test_song_without_todo():
    """Test that songs without TODO are not filtered."""
    song = SongInfo(
        name="Test Song",
        melody="Traditional",
        composer="John Doe",
        arranger="Jane Smith",
        lyrics="Verse 1\nVerse 2\nChorus",
        notes="Written in 1950"
    )
    assert song_contains_todo(song) is False


def test_song_with_none_fields():
    """Test that songs with None fields don't cause errors."""
    song = SongInfo(
        name="Test Song",
        melody=None,
        composer=None,
        arranger=None,
        lyrics="Some lyrics",
        notes=None
    )
    assert song_contains_todo(song) is False


def test_case_sensitive_todo():
    """Test that TODO detection is case-sensitive."""
    song = SongInfo(
        name="Test Song",
        melody=None,
        composer=None,
        arranger=None,
        lyrics="This has todo in lowercase",
        notes=None
    )
    assert song_contains_todo(song) is False
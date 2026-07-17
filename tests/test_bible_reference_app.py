import unittest
import tempfile
from pathlib import Path

import bible_reference_app as app


class BibleReferenceDataTests(unittest.TestCase):
    def test_canonical_book_name_accepts_common_variations(self):
        self.assertEqual(app.canonical_book_name("john"), "John")
        self.assertEqual(app.canonical_book_name("Jn"), "John")
        self.assertEqual(app.canonical_book_name("1Corinthians"), "1 Corinthians")
        self.assertEqual(app.canonical_book_name("psalms"), "Psalm")

    def test_normalize_bible_data_converts_chapter_keys(self):
        data = {
            "KJV": {
                "John": {
                    "3": ["For God so loved the world."],
                    "not-a-number": ["ignored"],
                }
            }
        }

        normalized = app.normalize_bible_data(data)

        self.assertEqual(normalized["KJV"]["John"][3], ["For God so loved the world."])
        self.assertNotIn("not-a-number", normalized["KJV"]["John"])

    def test_normalize_bible_data_ignores_malformed_shapes(self):
        self.assertEqual(app.normalize_bible_data(None), {})
        self.assertEqual(app.normalize_bible_data({"KJV": []}), {})

    def test_reference_range_parts_accepts_same_chapter_ranges(self):
        self.assertEqual(app.reference_range_parts("John 3:16-18"), ("John", 3, 16, 18))
        self.assertEqual(app.reference_range_parts("psalms 23:1 - 6"), ("Psalm", 23, 1, 6))
        self.assertIsNone(app.reference_range_parts("John 3:18-16"))

    def test_normalized_reference_formats_aliases_and_ranges(self):
        self.assertEqual(app.normalized_reference("Jn 1:1"), "John 1:1")
        self.assertEqual(app.normalized_reference("1Corinthians 13:1-4"), "1 Corinthians 13:1-4")

    def test_word_occurrences_returns_references_and_counts(self):
        translation = {
            "John": {
                1: [
                    "In the beginning was the Word, and the Word was with God.",
                    "The same was in the beginning with God.",
                ]
            },
            "Genesis": {
                1: ["And God said, Let there be light: and there was light."]
            },
        }

        matches = app.word_occurrences(translation, "word")

        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["reference"], "John 1:1")
        self.assertEqual(matches[0]["count"], 2)
        self.assertIn("Word", matches[0]["text"])

    def test_verse_text_from_translation_uses_requested_translation(self):
        app.BIBLE["TESTA"] = {"John": {1: ["Translation A text."]}}
        app.BIBLE["TESTB"] = {"John": {1: ["Translation B text."]}}
        try:
            self.assertEqual(app.verse_text_from_translation("TESTA", "John 1:1"), "Translation A text.")
            self.assertEqual(app.verse_text_from_translation("TESTB", "John 1:1"), "Translation B text.")
            self.assertEqual(app.verse_text_from_translation("TESTB", "John 1:2"), "")
        finally:
            app.BIBLE.pop("TESTA", None)
            app.BIBLE.pop("TESTB", None)

    def test_search_bible_supports_modes_ranges_and_relevance(self):
        translation = {
            "John": {1: ["Light light shines in darkness.", "The Word was with God."]},
            "Genesis": {1: ["Let there be light."]},
        }

        gospel_matches = app.search_bible(
            translation,
            "light",
            whole_word=True,
            books=app.GOSPEL_BOOKS,
            sort_mode="Relevance",
            context=True,
        )

        self.assertEqual([item["reference"] for item in gospel_matches], ["John 1:1"])
        self.assertEqual(gospel_matches[0]["count"], 2)

    def test_normalize_study_sessions_keeps_references_and_notes(self):
        sessions = app.normalize_study_sessions([
            {"name": "Romans 8 Study", "references": ["Jn 1:1"], "notes": "A note."}
        ])

        self.assertEqual(sessions[0]["name"], "Romans 8 Study")
        self.assertEqual(sessions[0]["references"], ["John 1:1"])
        self.assertEqual(sessions[0]["notes"], "A note.")

    def test_convert_text_document_to_library_item(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = tmp_path / "sample.txt"
            source.write_text("This is a converted study document.", encoding="utf-8")
            original_library_path = app.DOCUMENT_LIBRARY_PATH
            original_image_dir = app.DOCUMENT_IMAGE_DIR
            app.DOCUMENT_LIBRARY_PATH = tmp_path / "library.json"
            app.DOCUMENT_IMAGE_DIR = tmp_path / "images"
            try:
                item = app.convert_document_to_library_item(source, "Sample Document")
                documents = app.read_document_library()
            finally:
                app.DOCUMENT_LIBRARY_PATH = original_library_path
                app.DOCUMENT_IMAGE_DIR = original_image_dir

        self.assertEqual(item["title"], "Sample Document")
        self.assertIn("converted study document", item["text"])
        self.assertEqual(len(documents), 1)
        self.assertEqual(documents[0]["title"], "Sample Document")

    def test_parse_hymn_page_extracts_menu_item(self):
        text = "\n".join([
            "22 OPENING SONGS",
            "Jn 6:67-68, Heb 4:12 7 8 7 8 8 8",
            "Blessed Jesus at Thy Word",
            "Words: Tobias Clausnitzer, 1663.",
            "Music: Liebster Jesu wir Sind Hier.",
            "1. Blessed Jesus, at Thy Word",
        ])

        hymn = app.parse_hymn_page(text, 22)

        self.assertEqual(hymn["number"], 22)
        self.assertEqual(hymn["section"], "Opening Songs")
        self.assertEqual(hymn["title"], "Blessed Jesus at Thy Word")
        self.assertEqual(hymn["page"], 22)

    def test_parse_hymn_page_accepts_number_at_end_of_header(self):
        text = "\n".join([
            "CHRISTMAS 21",
            "Lk 2:1-20 7 6 7 6",
            "A Great and Mighty Wonder",
            "Words: Germanus of Constantinople.",
            "Music: Es Ist Ein Ros Entsprungen.",
        ])

        hymn = app.parse_hymn_page(text, 22)

        self.assertEqual(hymn["number"], 21)
        self.assertEqual(hymn["section"], "Christmas")
        self.assertEqual(hymn["title"], "A Great and Mighty Wonder")

    def test_normalize_study_data_accepts_json_language_shape(self):
        data = {
            "John 1:1": {
                "teaching": "Teaching",
                "cross": ["Genesis 1:1"],
                "language": [{"word": "Word", "original": "Logos", "note": "Greek term."}],
                "map": "Judea",
                "people": ["Jesus"],
                "places": ["Jerusalem"],
                "timeline": "First century",
            }
        }

        normalized = app.normalize_study_data(data)

        self.assertEqual(normalized["John 1:1"]["language"], [("Word", "Logos", "Greek term.")])
        self.assertEqual(normalized["John 1:1"]["people"], ["Jesus"])

    def test_normalize_people_data_accepts_person_profiles(self):
        data = {
            "Moses": {
                "canon": "Hebrew Bible",
                "category": "Prophets",
                "roles": ["prophet", "leader"],
                "summary": "Leader of Israel.",
                "references": ["exodus 3:1"],
                "related_people": ["Aaron"],
            }
        }

        normalized = app.normalize_people_data(data)

        self.assertEqual(normalized["Moses"]["references"], ["Exodus 3:1"])
        self.assertEqual(normalized["Moses"]["related_people"], ["Aaron"])

    def test_parse_people_text_file_extracts_profile_article_and_references(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "Mary_the_Mother_of_Jesus.txt"
            path.write_text(
                "Name: Mary the Mother of Jesus\n"
                "============================================================\n\n"
                "Mary the Mother of Jesus The mother of Jesus. She appears in Luke 1:26-56 and John 19:26.",
                encoding="utf-8",
            )

            profile = app.parse_people_text_file(path)

        self.assertEqual(profile["summary"], "The mother of Jesus.")
        self.assertIn("Luke 1:26-56", profile["references"])
        self.assertIn("John 19:26", profile["references"])
        self.assertIn("mother of Jesus", profile["article"])

    def test_merge_people_profiles_preserves_curated_fields_and_adds_article(self):
        base = {
            "Paul": {
                "canon": "New Testament",
                "category": "Apostles",
                "roles": ["apostle"],
                "summary": "Curated summary.",
                "references": ["Acts 9:1"],
                "related_people": [],
                "aliases": [],
                "article": "",
                "source": "",
            }
        }
        imported = {
            "Paul": {
                "canon": "New Testament",
                "category": "New Testament Figures",
                "roles": [],
                "summary": "Imported summary.",
                "references": ["Romans 1:1"],
                "related_people": [],
                "aliases": ["Saul of Tarsus"],
                "article": "Long imported article.",
                "source": "Paul.txt",
            }
        }

        merged = app.merge_people_profiles(base, imported)

        self.assertEqual(merged["Paul"]["summary"], "Curated summary.")
        self.assertIn("Romans 1:1", merged["Paul"]["references"])
        self.assertEqual(merged["Paul"]["article"], "Long imported article.")
        self.assertIn("Saul of Tarsus", merged["Paul"]["aliases"])

    def test_infer_map_metadata_from_filename(self):
        metadata = app.infer_map_metadata("Pauls First Missionary Journey")

        self.assertIn("Paul", metadata["related_people"])
        self.assertIn("Acts 13:4", metadata["related_passages"])
        self.assertEqual(metadata["period"], "Early church")

    def test_merge_discovered_maps_avoids_duplicate_titles(self):
        base = [{"title": "Pauls First Missionary Journey", "local_image": "", "related_people": []}]
        discovered = [{"title": "Pauls First Missionary Journey", "local_image": "map.png", "related_people": ["Paul"]}]

        merged = app.merge_discovered_maps(base, discovered)

        self.assertEqual(len(merged), 1)

    def test_parse_numbered_chapter_text_extracts_jps_style_verses(self):
        text = "The Holy Scriptures Chapter 1 1 In the beginning God created. 2 And the earth was unformed. {P}"

        verses = app.parse_numbered_chapter_text(text)

        self.assertEqual(verses, ["In the beginning God created.", "And the earth was unformed."])

    def test_jps_book_codes_cover_tanakh_books(self):
        missing = [book for book in app.TANAKH_BOOKS if book not in app.JPS_BOOK_CODES]

        self.assertEqual(missing, [])

    def test_bundled_kjv_file_can_be_normalized(self):
        path = app.BUNDLED_ENGLISH_DIR / "kjv.json"
        if not path.exists():
            self.skipTest("Bundled KJV data is not present")

        code, label, translation = app.normalize_bundled_bible_file(path)

        self.assertEqual(code, "KJV")
        self.assertIn("King James", label)
        self.assertIn("Genesis", translation)
        self.assertIn(1, translation["Genesis"])
        self.assertTrue(translation["Genesis"][1][0])

    def test_people_reference_data_has_expected_sections(self):
        normalized = app.normalize_people_reference_data(app.DEFAULT_PEOPLE_REFERENCE)

        self.assertIn("family_trees", normalized)
        self.assertIn("kings_timeline", normalized)
        self.assertIn("prophets_timeline", normalized)
        self.assertIn("apostles", normalized)
        self.assertTrue(normalized["family_trees"][0]["references"][0].startswith("Genesis"))


if __name__ == "__main__":
    unittest.main()

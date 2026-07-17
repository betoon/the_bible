import unittest
from threading import Event
from pathlib import Path
from unittest.mock import patch

from bible_app.config.settings import Settings
from bible_app.core.cache import BibleLookupCache, LruMemoryCache
from bible_app.core.references import normalized_reference, reference_range_parts
from bible_app.core.search import search_bible, word_occurrences
from bible_app.core.hymns import parse_hymn_page
from bible_app.core import documents as document_core
from bible_app.core import bible_data as bible_data_core
from bible_app.core.bible_data import parse_numbered_chapter_text
from bible_app.core.chapter_a_day import CHAPTER_A_DAY_PLAN_NAME
from bible_app.core.maps import infer_map_metadata, merge_discovered_maps
from bible_app.core.translations import normalize_bible_data, niv_chapter_segments
from bible_app.core.study_tools import (
    merge_people_profiles,
    normalize_people_data,
    normalize_study_data,
    parse_people_text_file,
)
from bible_app.storage.data_manager import read_json, write_json
from bible_app.storage.backup import BackupManager, usable_backup_dir
from bible_app.storage.models import BibleNote, JournalEntry
from bible_app.storage.user_data import (
    default_reading_plans,
    normalize_concepts,
    normalize_hymn_collection,
    normalize_reading_plans,
    normalize_recent_references,
    normalize_worksheets,
)
from bible_app.utils.validators import clean_reference, is_reference, validate_bible_reference
from bible_app.utils.background import BackgroundTaskRunner


class ImmediateRoot:
    def after(self, _delay, callback):
        callback()


class BibleAppModuleTests(unittest.TestCase):
    def test_config_settings_reads_ini_and_environment_overrides(self):
        config_path = Path("work/test_settings.ini")
        config_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            config_path.write_text(
                "[app]\napp_title = Custom Bible App\nwindow_width = 900\nwindow_height = 700\n"
                "[translations]\ndefault = ESV\n",
                encoding="utf-8",
            )
            settings = Settings(config_path)
            self.assertEqual(settings.app_title, "Custom Bible App")
            self.assertEqual(settings.window_geometry, "900x700")
            self.assertEqual(settings.default_translation, "ESV")
            with patch.dict("os.environ", {"BIBLE_APP_APP_APP_TITLE": "Env Bible App"}):
                self.assertEqual(Settings(config_path).app_title, "Env Bible App")
        finally:
            config_path.unlink(missing_ok=True)

    def test_lru_memory_cache_evicts_oldest_item(self):
        cache = LruMemoryCache(max_size=2)
        cache.set("a", 1)
        cache.set("b", 2)
        self.assertEqual(cache.get("a"), 1)
        cache.set("c", 3)
        self.assertIsNone(cache.get("b"))
        self.assertEqual(cache.get("c"), 3)

    def test_bible_lookup_cache_clears_by_translation(self):
        cache = BibleLookupCache(max_passages=4)
        cache.set_passage("KJV", "John 1:1", "text")
        cache.set_passage("ESV", "John 1:1", "other")
        cache.set_references("KJV", [("John 1:1", "text")])
        cache.clear("KJV")
        self.assertIsNone(cache.get_passage("KJV", "John 1:1"))
        self.assertEqual(cache.get_passage("ESV", "John 1:1"), "other")
        self.assertIsNone(cache.get_references("KJV"))

    def test_background_task_runner_reports_success_and_error(self):
        runner = BackgroundTaskRunner(ImmediateRoot(), max_workers=1)
        results = []
        errors = []
        success_ready = Event()
        error_ready = Event()

        def record_success(result):
            results.append(result)
            success_ready.set()

        def record_error(error):
            errors.append(error)
            error_ready.set()

        try:
            with patch("bible_app.utils.background.logger.exception"):
                ok_future = runner.submit(lambda: "ok", on_success=record_success)
                bad_future = runner.submit(lambda: (_ for _ in ()).throw(RuntimeError("bad")), on_error=record_error)
                ok_future.result(timeout=5)
                with self.assertRaises(RuntimeError):
                    bad_future.result(timeout=5)
                self.assertTrue(success_ready.wait(timeout=5))
                self.assertTrue(error_ready.wait(timeout=5))
        finally:
            runner.shutdown()
        self.assertEqual(results, ["ok"])
        self.assertEqual(str(errors[0]), "bad")

    def test_reference_helpers_normalize_aliases_and_ranges(self):
        self.assertEqual(normalized_reference("Jn 1:1"), "John 1:1")
        self.assertEqual(reference_range_parts("psalms 23:1-6"), ("Psalm", 23, 1, 6))

    def test_search_helpers_find_words_and_relevance(self):
        translation = {
            "John": {1: ["Light light shines.", "The Word was with God."]},
            "Genesis": {1: ["Let there be light."]},
        }
        self.assertEqual(word_occurrences(translation, "word")[0]["reference"], "John 1:2")
        results = search_bible(translation, "light", sort_mode="Relevance")
        self.assertEqual(results[0]["reference"], "John 1:1")

    def test_hymn_parser_extracts_score_page_title(self):
        text = "\n".join([
            "CHRISTMAS 21",
            "Lk 2:1-20 7 6 7 6",
            "A Great and Mighty Wonder",
            "Words: Germanus of Constantinople.",
            "Music: Es Ist Ein Ros Entsprungen.",
        ])
        hymn = parse_hymn_page(text, 22)
        self.assertEqual(hymn["title"], "A Great and Mighty Wonder")
        self.assertEqual(hymn["section"], "Christmas")

    def test_storage_round_trips_json(self):
        path = Path("work/test_storage_module.json")
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            write_json(path, {"ok": True}, make_backup=False)
            self.assertEqual(read_json(path, {}), {"ok": True})
        finally:
            path.unlink(missing_ok=True)

    def test_storage_quarantines_invalid_json(self):
        path = Path("work/bad_storage_module.json")
        quarantine_dir = usable_backup_dir() / "quarantine"
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            path.write_text("{bad json", encoding="utf-8")
            self.assertEqual(read_json(path, {"fallback": True}), {"fallback": True})
            quarantined = list(quarantine_dir.glob("bad_storage_module-invalid-json-*.json"))
            self.assertTrue(quarantined)
        finally:
            path.unlink(missing_ok=True)
            for item in quarantine_dir.glob("bad_storage_module-invalid-json-*.json"):
                item.unlink(missing_ok=True)

    def test_backup_manager_creates_and_rotates_backups(self):
        source = Path("work/source_data")
        backup_dir = Path("work/snapshot_backups")
        source.mkdir(parents=True, exist_ok=True)
        try:
            (source / "sample.json").write_text('{"ok": true}', encoding="utf-8")
            manager = BackupManager(backup_dir, max_backups=1)
            first = manager.create_backup(source)
            (source / "sample.json").write_text('{"ok": false}', encoding="utf-8")
            second = manager.create_backup(source)
            self.assertTrue(second.exists())
            self.assertFalse(first.exists())
            self.assertEqual(len(manager.list_backups()), 1)
        finally:
            if source.exists():
                for child in source.iterdir():
                    child.unlink(missing_ok=True)
                source.rmdir()
            if backup_dir.exists():
                for child in backup_dir.iterdir():
                    if child.is_dir():
                        for nested in child.iterdir():
                            nested.unlink(missing_ok=True)
                        child.rmdir()
                backup_dir.rmdir()

    def test_translation_helpers_normalize_and_split_chapters(self):
        normalized = normalize_bible_data({"KJV": {"John": {"1": [" In the beginning "]}}})
        self.assertEqual(normalized["KJV"]["John"][1], ["In the beginning"])
        self.assertEqual(niv_chapter_segments("1In the beginning 2Now the earth")[1], (2, "Now the earth"))

    def test_bible_data_parses_numbered_jps_text(self):
        verses = parse_numbered_chapter_text("Chapter 1 1 First verse. 2 Second verse.")
        self.assertEqual(verses, ["First verse.", "Second verse."])

    def test_bible_data_fetch_url_retries_transient_failures(self):
        calls = []
        original_urlopen = bible_data_core.urllib.request.urlopen
        original_sleep = bible_data_core.time.sleep

        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self):
                return b"ok"

        def fake_urlopen(_request, timeout=20):
            calls.append(timeout)
            if len(calls) == 1:
                raise OSError("temporary")
            return FakeResponse()

        try:
            bible_data_core.urllib.request.urlopen = fake_urlopen
            bible_data_core.time.sleep = lambda _seconds: None
            self.assertEqual(bible_data_core.fetch_url("https://example.test", timeout=1, max_retries=2), b"ok")
            self.assertEqual(len(calls), 2)
        finally:
            bible_data_core.urllib.request.urlopen = original_urlopen
            bible_data_core.time.sleep = original_sleep

    def test_user_data_normalizers_keep_study_data_clean(self):
        self.assertEqual(normalize_concepts({"bad": True}, [{"name": "Grace", "references": ["jn 1:1"]}])[0]["references"], ["John 1:1"])
        built_in_plans = default_reading_plans()
        chapter_a_day = next(plan for plan in built_in_plans if plan["name"] == CHAPTER_A_DAY_PLAN_NAME)
        self.assertEqual(len(chapter_a_day["references"]), 365)
        self.assertEqual(normalize_reading_plans([{"name": "Plan", "references": ["jn 1:1"], "completed": []}])[0]["references"], ["John 1:1"])
        self.assertEqual(normalize_worksheets({"John 1:1": {"observation": "Word"}})["John 1:1"]["observation"], "Word")
        self.assertEqual(len(normalize_hymn_collection([{"title": "Holy, Holy, Holy"}, {"title": "Holy, Holy, Holy"}])), 1)
        self.assertEqual(normalize_recent_references(["jn 1:1"])[0]["reference"], "John 1:1")

    def test_validators_accept_and_reject_references(self):
        self.assertEqual(validate_bible_reference("jn 3:16"), ("John", 3, 16))
        self.assertEqual(validate_bible_reference("psalms 23:1-6"), ("Psalm", 23, 1, 6))
        self.assertTrue(is_reference("Genesis 1:1"))
        self.assertEqual(clean_reference("rev 22:1"), "Revelation 22:1")
        with self.assertRaises(ValueError):
            validate_bible_reference("John 99:1")

    def test_storage_models_validate_required_fields(self):
        self.assertEqual(BibleNote("jn 1:1", "Note").to_dict()["reference"], "John 1:1")
        self.assertEqual(JournalEntry("ps 23:1", reflection="Prayerful thought").to_dict()["reference"], "Psalm 23:1")
        with self.assertRaises(ValueError):
            BibleNote("", "").validate()

    def test_study_tools_normalize_people_and_study_data(self):
        study = normalize_study_data({
            "John 1:1": {"language": [{"word": "Word", "original": "Logos", "note": "Greek"}], "people": ["Jesus"]}
        })
        people = normalize_people_data({"Moses": {"references": ["exodus 3:1"], "related_people": ["Aaron"]}})
        self.assertEqual(study["John 1:1"]["language"][0], ("Word", "Logos", "Greek"))
        self.assertEqual(people["Moses"]["references"], ["Exodus 3:1"])

    def test_study_tools_parse_and_merge_people_profiles(self):
        path = Path("work/Mary_the_Mother_of_Jesus.txt")
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            path.write_text(
                "Name: Mary the Mother of Jesus\n"
                "============================================================\n\n"
                "Mary the Mother of Jesus The mother of Jesus. She appears in Luke 1:26-56.",
                encoding="utf-8",
            )
            profile = parse_people_text_file(path)
        finally:
            path.unlink(missing_ok=True)
        merged = merge_people_profiles(
            {"Mary the Mother of Jesus": {"summary": "Curated.", "references": [], "aliases": [], "roles": [], "related_people": []}},
            {"Mary the Mother of Jesus": profile},
        )
        self.assertIn("Luke 1:26-56", merged["Mary the Mother of Jesus"]["references"])
        self.assertEqual(merged["Mary the Mother of Jesus"]["summary"], "Curated.")

    def test_map_helpers_infer_and_merge(self):
        metadata = infer_map_metadata("Pauls First Missionary Journey")
        self.assertIn("Paul", metadata["related_people"])
        merged = merge_discovered_maps(
            [{"title": "Pauls First Missionary Journey", "local_image": "", "related_people": []}],
            [{"title": "Pauls First Missionary Journey", "local_image": "map.png", "related_people": ["Paul"]}],
        )
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["local_image"], "map.png")

    def test_document_core_converts_text_document(self):
        source = Path("work/module_sample.txt")
        library_path = Path("work/module_library.json")
        image_dir = Path("work/module_images")
        original_library_path = document_core.DOCUMENT_LIBRARY_PATH
        original_image_dir = document_core.DOCUMENT_IMAGE_DIR
        source.parent.mkdir(parents=True, exist_ok=True)
        try:
            source.write_text("This is a module converted document.", encoding="utf-8")
            document_core.DOCUMENT_LIBRARY_PATH = library_path
            document_core.DOCUMENT_IMAGE_DIR = image_dir
            item = document_core.convert_document_to_library_item(source, "Module Sample")
            self.assertEqual(item["title"], "Module Sample")
            self.assertIn("module converted document", item["text"])
            self.assertEqual(len(document_core.read_document_library()), 1)
        finally:
            document_core.DOCUMENT_LIBRARY_PATH = original_library_path
            document_core.DOCUMENT_IMAGE_DIR = original_image_dir
            source.unlink(missing_ok=True)
            library_path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()

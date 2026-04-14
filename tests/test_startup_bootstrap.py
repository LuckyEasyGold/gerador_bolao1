import pytest

from backend import main


class DummySession:
    def __init__(self):
        self.rollback_called = False
        self.close_called = False

    def rollback(self):
        self.rollback_called = True

    def close(self):
        self.close_called = True


@pytest.mark.asyncio
async def test_bootstrap_contests_skips_when_database_has_data(monkeypatch):
    session = DummySession()

    class FakeRepository:
        def __init__(self, db):
            assert db is session

        def count(self):
            return 12

    class FakeImporter:
        def __init__(self, db):
            raise AssertionError("Importer não deve ser criado quando já há concursos")

    monkeypatch.setattr(main.settings, "auto_sync_contests_on_startup", True)
    monkeypatch.setattr(main, "SessionLocal", lambda: session)
    monkeypatch.setattr(main, "ContestRepository", FakeRepository)
    monkeypatch.setattr(main, "LotofacilDataImporter", FakeImporter)

    result = await main.bootstrap_contests_if_needed()

    assert result == {"status": "skipped", "existing_contests": 12}
    assert session.close_called is True
    assert session.rollback_called is False


@pytest.mark.asyncio
async def test_bootstrap_contests_imports_when_database_is_empty(monkeypatch):
    session = DummySession()

    class FakeRepository:
        def __init__(self, db):
            assert db is session

        def count(self):
            return 0

    class FakeImporter:
        def __init__(self, db):
            assert db is session

        async def sync_latest(self):
            return 3456

    monkeypatch.setattr(main.settings, "auto_sync_contests_on_startup", True)
    monkeypatch.setattr(main, "SessionLocal", lambda: session)
    monkeypatch.setattr(main, "ContestRepository", FakeRepository)
    monkeypatch.setattr(main, "LotofacilDataImporter", FakeImporter)

    result = await main.bootstrap_contests_if_needed()

    assert result == {"status": "imported", "imported_contests": 3456}
    assert session.close_called is True
    assert session.rollback_called is False


@pytest.mark.asyncio
async def test_bootstrap_contests_handles_sync_failures(monkeypatch):
    session = DummySession()

    class FakeRepository:
        def __init__(self, db):
            assert db is session

        def count(self):
            return 0

    class FakeImporter:
        def __init__(self, db):
            assert db is session

        async def sync_latest(self):
            raise RuntimeError("API indisponível")

    monkeypatch.setattr(main.settings, "auto_sync_contests_on_startup", True)
    monkeypatch.setattr(main, "SessionLocal", lambda: session)
    monkeypatch.setattr(main, "ContestRepository", FakeRepository)
    monkeypatch.setattr(main, "LotofacilDataImporter", FakeImporter)

    result = await main.bootstrap_contests_if_needed()

    assert result == {"status": "failed", "error": "API indisponível"}
    assert session.close_called is True
    assert session.rollback_called is True

from app.security_events import EventCollector


def test_source_is_hashed():
    collector = EventCollector()

    event = collector.record(
        event_type="canary_access",
        source="192.0.2.1",
        route="/__canary__/status",
        method="GET",
    )

    assert event.source_hash != "192.0.2.1"
    assert len(event.source_hash) == 64
    assert len(collector.snapshot()) == 1

import pytest

from devhub.events import Event, EventBus


def test_event_normalizes_name_and_has_platform_id():
    event = Event(" Resource.Updated ", {"resource_id": "RES-1"})

    assert event.name == "resource.updated"
    assert event.event_id.startswith("EVT-")
    assert event.payload["resource_id"] == "RES-1"


def test_publish_delivers_to_named_and_wildcard_subscribers():
    bus = EventBus()
    received = []

    bus.subscribe("resource.updated", received.append)
    bus.subscribe("*", received.append)

    delivered = bus.publish(Event("resource.updated"))

    assert delivered == 2
    assert len(received) == 2


def test_unsubscribe_stops_delivery():
    bus = EventBus()
    received = []
    subscription = bus.subscribe("workflow.completed", received.append)

    assert bus.unsubscribe(subscription) is True
    assert bus.unsubscribe(subscription) is False
    assert bus.publish(Event("workflow.completed")) == 0
    assert received == []


def test_duplicate_subscription_is_not_registered_twice():
    bus = EventBus()
    received = []

    bus.subscribe("knowledge.updated", received.append)
    bus.subscribe("knowledge.updated", received.append)

    assert bus.subscriber_count("knowledge.updated") == 1
    assert bus.publish(Event("knowledge.updated")) == 1


def test_invalid_event_name_is_rejected():
    with pytest.raises(ValueError):
        Event("invalid")

    with pytest.raises(ValueError):
        EventBus().subscribe("invalid", lambda event: None)

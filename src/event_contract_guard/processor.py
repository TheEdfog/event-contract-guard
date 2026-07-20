import json
from collections.abc import Callable
from typing import Any

from event_contract_guard.contracts import ContractStore
from event_contract_guard.validation import quarantine_record, validate_event


def route_event(
    *,
    subject: str,
    payload: dict[str, Any],
    store: ContractStore,
    publish_valid: Callable[[dict[str, Any]], None],
    publish_quarantine: Callable[[dict[str, Any]], None],
) -> bool:
    """Route one decoded event. Kafka adapters only handle offsets and serialization."""
    result = validate_event(store.load(subject), payload)
    if result.accepted:
        publish_valid(payload)
        return True
    publish_quarantine(quarantine_record(subject=subject, payload=payload, errors=result.errors))
    return False


def run_kafka_worker(
    *,
    bootstrap_servers: str,
    subject: str,
    source_topic: str,
    valid_topic: str,
    quarantine_topic: str,
    store: ContractStore,
) -> None:
    from confluent_kafka import Consumer, Producer

    consumer = Consumer(
        {
            "bootstrap.servers": bootstrap_servers,
            "group.id": f"contract-guard-{subject}",
            "enable.auto.commit": False,
            "auto.offset.reset": "earliest",
        }
    )
    producer = Producer({"bootstrap.servers": bootstrap_servers, "enable.idempotence": True})
    consumer.subscribe([source_topic])
    try:
        while True:
            message = consumer.poll(1.0)
            if message is None:
                continue
            if message.error():
                raise RuntimeError(message.error())
            payload = json.loads(message.value())
            route_event(
                subject=subject,
                payload=payload,
                store=store,
                publish_valid=lambda value: producer.produce(valid_topic, value=json.dumps(value)),
                publish_quarantine=lambda value: producer.produce(
                    quarantine_topic, value=json.dumps(value)
                ),
            )
            producer.flush(10)
            consumer.commit(message=message, asynchronous=False)
    finally:
        consumer.close()

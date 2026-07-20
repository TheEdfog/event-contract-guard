# Event Contract Guard

Event Contract Guard is a small service for teams that exchange JSON events through Kafka. It validates payloads at runtime, explains incompatible schema changes before release and routes rejected messages to a quarantine topic without committing the source offset early.

It addresses a common ownership gap: producers know their application model, consumers know their analytical requirements, but neither side has an executable agreement about the event between them.

## What it does

- stores versioned JSON Schema contracts with an explicit owner;
- validates events through an HTTP API, CLI or Kafka worker;
- checks backward compatibility for removed fields, new required fields, type changes and narrowed enums;
- returns a structured quarantine envelope instead of a generic exception;
- exposes Prometheus counters for accepted and rejected events;
- includes a non-root Docker image and a small Helm chart with probes and resource limits.

The Kafka adapter disables automatic offset commits. It publishes the accepted or quarantined record first and commits the source offset only after the producer flush succeeds. The validation and routing logic is independent of Kafka, which keeps unit tests fast.

## Local run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn event_contract_guard.api:app --reload
```

Validate an event:

```bash
curl -X POST http://localhost:8000/validate/retail.orders.v1 \
  -H "Content-Type: application/json" \
  --data @event.json
```

Check a candidate schema before merging it:

```bash
contract-guard retail.orders.v1 candidate-schema.json --schema
```

The API also exposes `/compatibility/{subject}`, `/contracts`, `/health` and `/metrics`.

## Deployment

```bash
docker compose up --build
helm template contract-guard helm/event-contract-guard
```

The included chart demonstrates the deployment boundary; it does not pretend to be a complete platform chart. A real environment should mount contracts from a versioned artifact or ConfigMap, configure authentication, add a PodDisruptionBudget and publish the image through the company registry.

## Tests

```bash
pip install -e ".[dev]"
ruff check .
pytest -q
docker compose config --quiet
```

## Deliberate limits

The compatibility checker implements a small, top-level subset appropriate for this example. JSON Schema `default` values are annotations, so a new required field is treated as breaking even when it declares a default. Production teams should use a mature Schema Registry or a standard such as the Data Contract Specification for nested compatibility rules and governance workflows.

The project was informed by the public Confluent Schema Registry patterns, the Data Contract Specification and OpenLineage's dataset ownership model. It is an independent implementation and does not copy source code from those projects.

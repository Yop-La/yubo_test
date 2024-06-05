# yubo_test

## Overview

The project currently includes the following components:

1. **PostgreSQL**: A database with two initialized tables.
2. **Redis**: An in-memory data cache.
3. **Kafka**: A message broker with an initialized topic named `live_views`.
4. **Python Server**: Hosts an API with two routes:
    - `GET /`: Returns "hello".
    - `POST /views`: Sends views to kafka topic named `live_views`. Then the view is consumed and persisted in PostgreSQL and Redis ( only a counter of the number of total views is updated )
    - `GET /profiles/{profileId}/views/live`: to get the number of views of a profile generated during a live 

## Project Setup and Launch

To launch the project, follow these steps:

1. **Start the Docker services**:
    ```bash
    docker-compose up --build -d
    ```

    This command builds and starts the necessary Docker containers in detached mode.

## Testing the project

Once the project is running, you can send some test views using the following `curl` command:

```bash
curl -X POST http://localhost:8000/views \
    -H "Content-Type: application/json" \
    -d '{
        "viewer_profile_id": 1,
        "viewed_profile_id": 2,
        "timestamp": "2023-01-01T12:00:00",
        "session_id": "sess123"
    }'
```

You can check that the view is sent in the corresponding kakfka topic with that command

```bash
docker exec -it yubo_test-kafka-1 /bin/kafka-console-consumer --bootstrap-server localhost:9092 --topic live_views --from-beginning
```

To check data in postgres

```bash
docker exec -it yubo_test-postgres-1 psql -U user -d mydatabase
```

To get the total number of views of a live  in real-time
```bash
curl -X GET "http://localhost:8000/profiles/1/views/live?sessionId=sess123"
```
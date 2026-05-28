# Week 2 Architecture
API accepts generation requests, persists job artifact snapshots, and a background worker dequeues and processes queued jobs. Data flow: request -> validate -> persist queued job -> worker running -> pipeline -> persist completed/failed state and result.

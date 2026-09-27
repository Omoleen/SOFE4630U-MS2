# SOFE4630U Milestone 2 Report
## Data Storage with Kubernetes, MySQL, Redis and Sink Connectors

**Name:** Emmanuel Omole  
**Student number:** 101004432  
**Date:** 2026-09-27  

**GitHub repository:** https://github.com/Omoleen/SOFE4630U-MS2

---

## 1. Environment

| Item | Value |
| --- | --- |
| GCP project | `clarity-staging-4afe8` |
| GKE cluster | `sofe4630u`, 3 x `e2-small` nodes, 20 GB disk, `northamerica-northeast2-a` |
| MySQL | `mysql-deployment` + LoadBalancer `mysql-service`, port 3306, schema `Readings` |
| Redis | `redis` deployment + LoadBalancer service, port 6379 |
| Topics | `smartMeterReadings`, `Image2Redis`, `weatherLabels`, `weatherStored` |

Both servers run as single-replica deployments, so the LoadBalancer has only one
pod to send traffic to. Its only job here is to give the pod a stable external IP.

## 2. Lab steps

**MySQL.** The `meterType` table was created with three rows, and
`select * from meterType where cost>=110` returned the `denver` and `losang` rows.

**Redis.** The commands run against database 0:

| Command | Effect |
| --- | --- |
| `select 0` | Switch to database 0 (Redis has 16, numbered 0 to 15). |
| `set var 100` | Store the value `100` under the key `var`. |
| `get var` | Read the value of `var`, returns `100`. |
| `keys *` | List every key in the database, returns `var`. |
| `del var` | Delete `var`, returns `1` (one key removed). |
| `keys *` | Returns an empty list. |

`SendImage.py` stored `ontarioTech.jpg` under the key `OntarioTech` and
`ReceiveImage.py` wrote it back out byte for byte identical.

**Sink connectors.** `mysql-connector` and `redis-connector` were created in
Integration Connectors (Toronto, 2 nodes), each fed by an Application Integration
flow: Cloud Pub/Sub trigger, Data Mapping, connector task. The MySQL flow inserts
each `smartMeterReadings` message into `SmartMeter` with the Create operation. The
Redis flow maps the message data to the value and the ordering key to the key, so
`produceImage.py` ends up with the base64 image stored under `image`. Both
integrations were unpublished and both connectors suspended after testing.

## 3. Discussion

### 3.1 Source and sink connectors

Both move data between a messaging system and an external system without custom
code. They differ in direction.

- A **source connector** reads from an external system, such as a database, a SaaS
  application or a file store, and publishes what it reads to a topic. A MySQL
  source connector, for example, turns new or changed rows into messages.
- A **sink connector** subscribes to a topic and writes every message into an
  external system. The connectors in this milestone are sinks: they take
  `smartMeterReadings` and `Image2Redis` messages and write them to MySQL and Redis.

A pipeline often uses both: a source brings data into the topic, processing stages
act on it, and a sink stores the result.

### 3.2 Applications of connectors

- **Persisting streams.** Storing sensor or event data in a database or warehouse
  (MySQL, BigQuery) for later queries and reporting.
- **Caching.** Keeping a fast store such as Redis up to date with the latest value
  per key, for example the last reading of each meter.
- **Database replication and migration.** A source on one database plus a sink on
  another copies changes between them (change data capture).
- **Integrating SaaS systems.** Moving records between applications such as
  Salesforce or ServiceNow and internal systems without writing their APIs by hand.
- **Feeding analytics and search.** Loading events into analytics tools, search
  indexes or Cloud Storage archives.
- **Decoupling services.** Producers publish once and each downstream store gets
  its own connector, so adding a new store does not change the producer.

## 4. Design

### 4.1 Pipeline

The Milestone 1 design sent the `Labels.csv` records straight from a producer to a
consumer. A storing stage now sits between them:

```
csvProducer.py -> weatherLabels -> storeStage.py -> weatherStored -> csvConsumer.py
                                        |
                                        v
                          MySQL on GKE (Readings.WeatherLabels)
```

| Script | Role |
| --- | --- |
| `csvProducer.py` | Unchanged from Milestone 1. Publishes each CSV row as JSON to `weatherLabels`. |
| `storeStage.py` | Subscribes to `weatherLabels-sub`, inserts the record into `WeatherLabels`, adds the generated `ID` to the record and publishes it to `weatherStored`. |
| `csvConsumer.py` | Same consumer as Milestone 1, now subscribed to `weatherStored-sub`. |

### 4.2 Choices

**MySQL rather than Redis.** The records are rows with a fixed set of numeric
fields, and the useful questions about them are queries: all readings for one
profile, averages, readings with a missing value. MySQL answers those with SQL.
Redis only looks values up by key, which suits the image case in the lab but not
this data.

**A Python stage rather than Application Integration.** The Application
Integration and Integration Connectors flow from Section 2 also works for this
data, but it bills for connector nodes for as long as it runs, which is why the
lab asks for it to be unpublished and suspended after testing. A small subscriber
does the same insert at no extra cost, keeps the logic in the repository, and can
forward the record to the consumer after storing it, which the sink connector
cannot.

**Key and missing values.** The CSV has no unique field, so `ID` is an
`auto_increment` primary key assigned by MySQL. Empty CSV cells arrive as `None`
and are stored as `NULL`.

**Delivery.** The stage acknowledges a message only after the insert and the
forward succeed. If it crashes before that, Pub/Sub redelivers the message instead
of dropping it. The Pub/Sub callback runs on several threads, so access to the
single MySQL connection is guarded by a lock.

### 4.3 Result

With all three scripts running, the producer published 100 records. The store
stage inserted 100 rows (IDs 1 to 100, 6 of them with a `NULL` temperature) and the
consumer printed 100 records, each carrying its database `ID`:

```
Consumed record:
   time : 1768708698.4967296
   profileName : denver
   temperature : 34.02835171306374
   humidity : 38.63135893990154
   pressure : None
   ID : 1
```

`select count(*) from WeatherLabels` returned 100.

## 5. Conclusion

MySQL and Redis were deployed on GKE and reached through LoadBalancer services, and
sink connectors were built for both with Application Integration. The design adds
a storing stage that persists every record in MySQL before passing it on, so the
data survives after the consumer has read it.

# SOFE4630U Milestone 2: Data Storage (Kubernetes, MySQL, Redis, Connectors)

**Name:** Emmanuel Omole  
**Student number:** 101004432

GCP project: `clarity-staging-4afe8`, GKE cluster `sofe4630u` in `northamerica-northeast2-a`.

## Layout

| Path | Purpose |
| --- | --- |
| `mySQL/` | Deployment and LoadBalancer service for the MySQL server. |
| `Redis/redis.yaml` | Deployment and LoadBalancer service for the Redis server. |
| `Redis/code/` | `SendImage.py` / `ReceiveImage.py`, store and read an image in Redis directly. |
| `MySQL-connector/smartMeter.py` | Publishes smart meter readings to `smartMeterReadings` for the MySQL sink connector. |
| `Redis-connector/` | `produceImage.py` publishes a base64 image to `Image2Redis`, `ReceiveImage.py` reads it back from Redis. |
| `Design/csvProducer.py` | Reads `Labels.csv` and publishes each record to `weatherLabels`. |
| `Design/storeStage.py` | Middle stage. Consumes `weatherLabels-sub`, inserts each record into the MySQL table `WeatherLabels`, then forwards it with its database ID to `weatherStored`. |
| `Design/csvConsumer.py` | Consumes `weatherStored-sub` and prints each stored record. |

## Design pipeline

```
csvProducer.py -> weatherLabels -> storeStage.py -> weatherStored -> csvConsumer.py
                                        |
                                        v
                          MySQL on GKE (Readings.WeatherLabels)
```

## Running

1. Deploy the servers:

   ```shell
   kubectl create -f mySQL/mysql-deploy.yaml
   kubectl create -f mySQL/mysql-service.yaml
   kubectl create -f Redis/redis.yaml
   kubectl get services      # note the external IPs
   ```

2. Install the libraries:

   ```shell
   pip install google-cloud-pubsub numpy redis pymysql
   ```

3. Copy the service account JSON key into the script folder and set the server IP
   (`mysql_ip` or `ip`) at the top of the script.
4. Design part, each in its own terminal:

   ```shell
   cd Design
   python csvConsumer.py     # terminal 1
   python storeStage.py      # terminal 2
   python csvProducer.py     # terminal 3
   ```

The key file is excluded by `.gitignore` and is not part of this repository.

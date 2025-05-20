# Movie Review Aggregator

## Monitor system

### How to use this

1. After built docker-compose successfully, you can access grafana dashboard:
    ```sh
        http://localhost:4000
    ```

2. Login to grafana with default username, password:

    ```sh
        username: admin
        password: admin
    ```

3. Change your username, password

4. At main dashboard:

    ```sh
        click Connections -> Data sources -> prometheus
    ```

5. Set url connection with corresponding prometheus url:

    ```sh
        http://prometheus:9090
    ```

6. Save & test

7. Then you can build your dashboard to monitor your system

    ```sh
        Dashboards -> New -> New dashboard -> Import dashboard -> Save dashboard
    ```

8. After saving your dashboard with your title, you can import dashboard from grafana dashboard:

    ```sh
        https://grafana.com/grafana/dashboards/
    ```

9. At your grafana dashboard, you can import prebuilt dashboard by id or url (ex: id = 1860)
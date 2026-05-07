# Using Sysbench

Install sysbench dependencies. On openEuler:
```bash
sudo dnf install mariadb-server mariadb-devel postgresql-server postgresql-server-devel libpq-devel
```

Install sysbench from git tree using:
```bash
sudo helpers/configure-sysbench.sh
```

To run just one instance in bare metal host, run:
```bash
sudo helpers/prepare_sysbench.sh
```

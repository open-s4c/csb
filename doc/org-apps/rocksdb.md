# Compiling RocksDB on OpenEuler

First, run the following instructions:
```bash
mkdir -p bm-external
cd bm-external
git clone https://github.com/facebook/rocksdb.git
cd rocksdb
git submodule update --init --recursive
git checkout v10.5.1 # A stable version with no compilation errors

sudo dnf install -y gflags gflags-devel snappy snappy-devel
```

If necessary, add the line `DISABLE_WARNING_AS_ERROR=1` into the Makefile.


Finally, run the following conclude its installation:
```bash
make -j release
# File db_bench is used in bm
```

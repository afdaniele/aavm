# aavm

**AAVM** - **A**lmost **A** **V**irtual **M**achine \
Docker Containers that want to be Virtual Machines.


## Developer

### Build a Runtime

You can build a runtime using the command,

```shell
cpk build
```

### Test run a Runtime

You can test run a runtime using the command,

```shell
cpk run -f -M -- --tmpfs /tmp --tmpfs /run --tmpfs /run/lock -v /sys/fs/cgroup:/sys/fs/cgroup:ro --privileged
```

# MLPerf Inference - Image Classification - NVIDIA TensorRT

[This image]() is based on
[the TensorRT 19.12 image](https://docs.nvidia.com/deeplearning/sdk/tensorrt-container-release-notes/rel_19-12.html) from NVIDIA
(which is in turn based on Ubuntu 18.04) with [CUDA](https://developer.nvidia.com/cuda-zone) 10.2 and [TensorRT](https://developer.nvidia.com/tensorrt) 6.0.1.

1. [Setup](#setup)
    - [Set up NVIDIA Docker](#setup_nvidia)
    - [Set up Collective Knowledge](#setup_ck)
    - [Download](#image_download) and/or [Build](#image_build) images
1. [Usage](#usage)
    - [Run once](#run)
    - [Benchmark](#benchmark)
        - [Docker parameters](#parameters_docker)
        - [LoadGen parameters](#parameters_loadgen)
    - [Explore](#explore)
    - [Analyze](#analyze)

<a name="setup"></a>
# Setup

<a name="setup_nvidia"></a>
## Set up NVIDIA Docker

As our GPU image is based on [nvidia-docker](https://github.com/NVIDIA/nvidia-docker), please follow instructions there to set up your system.

Note that you may need to run commands below with `sudo`, unless you [manage Docker as a non-root user](https://docs.docker.com/install/linux/linux-postinstall/#manage-docker-as-a-non-root-user).

<a name="setup_ck"></a>
## Set up Collective Knowledge

You will need to install [Collective Knowledge](http://cknowledge.org) to build images and save benchmarking results.
Please follow the [CK installation instructions](https://github.com/ctuning/ck#installation) and then pull this CK-MLPerf repository:
```bash
$ ck pull repo:ck-mlperf
```

To refresh all CK repositories after any updates (e.g. bug fixes), run:
```bash
$ ck pull all
```
**NB:** This only updates CK repositories on the host system. To update the Docker image, [rebuild](#build) it using the `--no-cache` flag.

### Set up environment variables

Set up the variable to this Docker image name:
```bash
$ export CK_IMAGE=image-classification-tensorrt-loadgen-py.tensorrt-6
```

Set up the variable that points to the directory that contains your CK repositories (usually `~/CK` or `~/CK_REPOS`):
```bash
$ export CK_REPOS=${HOME}/CK
```

<a name="image_download"></a>
## Download from Docker Hub

To download a prebuilt image from Docker Hub, run:
```
$ docker pull ctuning/${CK_IMAGE}
```

<a name="image_build"></a>
## Build

To build an image on your system, run:
```bash
$ ck build docker:${CK_IMAGE}
```

**NB:** This CK command is equivalent to:
```bash
$ cd `ck find docker:${CK_IMAGE}`
$ docker build --no-cache -f Dockerfile -t ctuning/${CK_IMAGE} .
```

<a name="usage"></a>
# Usage

<a name="run"></a>
## Run inference once

Once you have downloaded or built an image, you can run inference in the accuracy or performance mode as follows.

### Accuracy mode

```bash
$ docker run --runtime=nvidia --env-file ${CK_REPOS}/ck-mlperf/docker/${CK_IMAGE}/env.list --rm ctuning/${CK_IMAGE} \
  "ck run program:image-classification-tensorrt-loadgen-py --skip_print_timers --env.CK_SILENT_MODE \
  --env.CK_LOADGEN_MODE=AccuracyOnly --env.CK_LOADGEN_SCENARIO=MultiStream \
  --env.CK_LOADGEN_MULTISTREAMNESS=32 --env.CK_BATCH_SIZE=32 \
  --env.CK_LOADGEN_DATASET_SIZE=500 --env.CK_LOADGEN_BUFFER_SIZE=500 \
  --env.CK_LOADGEN_CONF_FILE=/home/dvdt/CK_REPOS/ck-mlperf/program/image-classification-tensorrt-loadgen-py/user.conf \
  --dep_add_tags.weights=model,tensorrt,resnet,converted-from-onnx,fp32,maxbatch.32 \
  && echo '--------------------------------------------------------------------------------' \
  && echo 'mlperf_log_summary.txt' \
  && echo '--------------------------------------------------------------------------------' \
  && cat  /home/dvdt/CK_REPOS/ck-mlperf/program/image-classification-tensorrt-loadgen-py/tmp/mlperf_log_summary.txt \
  && echo '--------------------------------------------------------------------------------' \
  && echo 'mlperf_log_detail.txt' \
  && echo '--------------------------------------------------------------------------------' \
  && cat  /home/dvdt/CK_REPOS/ck-mlperf/program/image-classification-tensorrt-loadgen-py/tmp/mlperf_log_detail.txt \
  && echo ''"
...
--------------------------------
accuracy=75.200%, good=376, total=500

--------------------------------
...
--------------------------------------------------------------------------------
mlperf_log_summary.txt
--------------------------------------------------------------------------------

No warnings encountered during test.

No errors encountered during test.
```

Here, we run inference on 500 images using a TensorRT plan converted on-the-fly
from the reference ResNet ONNX model.

**NB:** This is equivalent to the default run command:
```bash
$ docker run --rm ctuning/$CK_IMAGE
```

#### Performance mode

```bash
$ docker run --runtime=nvidia --env-file ${CK_REPOS}/ck-mlperf/docker/${CK_IMAGE}/env.list --rm ctuning/${CK_IMAGE} \
  "ck run program:image-classification-tensorrt-loadgen-py --skip_print_timers --env.CK_SILENT_MODE \
  --env.CK_LOADGEN_MODE=PerformanceOnly --env.CK_LOADGEN_SCENARIO=MultiStream \
  --env.CK_LOADGEN_MULTISTREAMNESS=32 --env.CK_BATCH_SIZE=32 \
  --env.CK_LOADGEN_COUNT_OVERRIDE=1440 \
  --env.CK_LOADGEN_DATASET_SIZE=500 --env.CK_LOADGEN_BUFFER_SIZE=1024 \
  --env.CK_LOADGEN_CONF_FILE=/home/dvdt/CK_REPOS/ck-mlperf/program/image-classification-tensorrt-loadgen-py/user.conf \
  --dep_add_tags.weights=model,tensorrt,resnet,converted-from-onnx,fp32,maxbatch.32 \
  && echo '--------------------------------------------------------------------------------' \
  && echo 'mlperf_log_summary.txt' \
  && echo '--------------------------------------------------------------------------------' \
  && cat  /home/dvdt/CK_REPOS/ck-mlperf/program/image-classification-tensorrt-loadgen-py/tmp/mlperf_log_summary.txt \
  && echo '--------------------------------------------------------------------------------' \
  && echo 'mlperf_log_detail.txt' \
  && echo '--------------------------------------------------------------------------------' \
  && cat  /home/dvdt/CK_REPOS/ck-mlperf/program/image-classification-tensorrt-loadgen-py/tmp/mlperf_log_detail.txt \
  && echo ''"
...
--------------------------------------------------------------------
|                LATENCIES (in milliseconds and fps)               |
--------------------------------------------------------------------
Number of samples run:           46080
Min latency:                     46.68 ms   (21.420 fps)
Median latency:                  48.96 ms   (20.427 fps)
Average latency:                 50.00 ms   (20.000 fps)
90 percentile latency:           53.00 ms   (18.869 fps)
99 percentile latency:           53.64 ms   (18.641 fps)
Max latency:                     57.20 ms   (17.481 fps)
--------------------------------------------------------------------
...
================================================
MLPerf Results Summary
================================================
SUT name : PySUT
Scenario : Multi Stream
Mode     : Performance
Samples per query : 32
Result is : INVALID
  Performance constraints satisfied : NO
  Min duration satisfied : Yes
  Min queries satisfied : Yes
Recommendations:
 * Reduce samples per query to improve latency.
...
```

In this example (on the NVIDIA GTX1080), the 99th percentile latency exceeds 50 ms,
which unfortunately makes the performance run **INVALID** according to the
[MLPerf Inference rules](https://github.com/mlperf/inference_policies/blob/master/inference_rules.adoc#41-benchmarks)
for the ResNet workload in the MultiStream scenario. As per the LoadGen recommendation, the number of samples per query (32 in the above example), should be reduced.
However, we do not know whether it should be reduced by only one sample per query or more.
To find out, we should benchmark this workload with several values of this parameter, and analyze the results.


<a name="benchmark"></a>
## Benchmark with parameters

When you run inference using `ck run`, the results get printed but not saved.
You can use `ck benchmark` to save the results on the host system as CK experiment entries (JSON files).

Create a directory on the host computer where you want to store experiment entries e.g.:
```bash
$ export CK_EXPERIMENTS_DIR=/data/$USER/tensorrt-experiments
$ mkdir -p ${CK_EXPERIMENTS_DIR}
```
(**NB:** `USER` must have write access to this directory.)

When running `ck benchmark` via Docker, map the internal directory `/home/dvdt/CK_REPOS/local/experiment` to `$CK_EXPERIMENTS_DIR` on the host:

```bash
$ export NUM_STREAMS=30
$ docker run --runtime=nvidia --env-file ${CK_REPOS}/ck-mlperf/docker/${CK_IMAGE}/env.list \
  --user=$(id -u):1500 --volume ${CK_EXPERIMENTS_DIR}:/home/dvdt/CK_REPOS/local/experiment \
  --rm ctuning/${CK_IMAGE} \
  "ck benchmark program:image-classification-tensorrt-loadgen-py --repetitions=1 --env.CK_SILENT_MODE \
  --env.CK_LOADGEN_MODE=PerformanceOnly --env.CK_LOADGEN_SCENARIO=MultiStream \
  --env.CK_LOADGEN_MULTISTREAMNESS=${NUM_STREAMS} --env.CK_BATCH_SIZE=${NUM_STREAMS} \
  --env.CK_LOADGEN_COUNT_OVERRIDE=1440 \
  --env.CK_LOADGEN_DATASET_SIZE=500 --env.CK_LOADGEN_BUFFER_SIZE=1024 \
  --env.CK_LOADGEN_CONF_FILE=/home/dvdt/CK_REPOS/ck-mlperf/program/image-classification-tensorrt-loadgen-py/user.conf \
  --dep_add_tags.weights=model,tensorrt,resnet,converted-from-onnx,fp32,maxbatch.${NUM_STREAMS} \
  --record --record_repo=local \
  --record_uoa=mlperf.closed.image-classification.tensorrt.resnet.multistream.performance \
  --tags=mlperf,closed,image-classification,tensorrt,resnet,multistream,performance \
  --skip_print_timers --skip_stat_analysis --process_multi_keys"
...
--------------------------------------------------------------------
|                LATENCIES (in milliseconds and fps)               |
--------------------------------------------------------------------
Number of samples run:           43200
Min latency:                     43.52 ms   (22.977 fps)
Median latency:                  44.74 ms   (22.350 fps)
Average latency:                 44.00 ms   (22.727 fps)
90 percentile latency:           45.21 ms   (22.120 fps)
99 percentile latency:           45.61 ms   (21.926 fps)
Max latency:                     52.87 ms   (18.914 fps)
--------------------------------------------------------------------
...
================================================
MLPerf Results Summary
================================================
SUT name : PySUT
Scenario : Multi Stream
Mode     : Performance
Samples per query : 30
Result is : INVALID
  Performance constraints satisfied : Yes
  Min duration satisfied : Yes
  Min queries satisfied : Yes
```

<a name="parameters_docker"></a>
### Docker parameters explained

#### `--env-file ${CK_REPOS}/ck-mlperf/docker/${CK_IMAGE}/env.list`

The path to an `env.list` file, which is usually located in the same directory as `Dockerfile`.

The `env.list` files are currently identical for all [dividiti](http://dividiti.com)'s images:
```
HOME=/home/dvdt
CK_ROOT=/home/dvdt/CK
CK_REPOS=/home/dvdt/CK_REPOS
CK_TOOLS=/home/dvdt/CK_TOOLS
PATH=/bin:/home/dvdt/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
CK_PYTHON=python3
CK_CC=gcc
GIT_USER="dividiti"
GIT_EMAIL="info@dividiti.com"
LANG=C.UTF-8
```

#### `--user=$(id -u):1500`

`id -u` returns your user id on the host system (`USER`). `1500` is the fixed
group id of the `dvdtg` group in the image. When you launch a container with
this parameter, your can access all files accessible to the `dvdtg` group.


#### `--volume ${CK_EXPERIMENTS_DIR}:/home/dvdt/CK_REPOS/local/experiment`

`CK_EXPERIMENTS_DIR` is a directory with read/write permissions for the user
that serves as shared space ("volume") between the host and the container.
This directory gets mapped to the `/home/dvdt/CK_REPOS/local/experiment`
directory in the image, which belongs to the `dvdt` user but is also made
accessible to the `dvdtg` group.  Therefore, you can retrieve from
`${CK_EXPERIMENTS_DIR}` the results of a container run, which receive your user
id and the `1500` group id.


<a name="parameters_loadgen"></a>
### LoadGen parameters
**TODO**


<a name="explore"></a>
## Explore

```bash
$ export CK_REPOS=$HOME/CK
$ export CK_IMAGE=`ck find ck-mlperf:experiment:image-classification-tensorrt-loadgen-py.tensorrt-6
$ export CK_EXPERIMENTS_DIR=$HOME/tensorrt-experiments
$ cd `ck find ck-mlperf:docker:${CK_IMAGE}`
$ CK_BATCH_SIZES="1 30 31 32" ./explore.sh
```

The results get accumulated under `$CK_EXPERIMENTS_DIR`:
```
$ ls -la $CK_EXPERIMENTS_DIR
total 16
drwxrwxr-x  4 anton dvdt  4096 Mar 28 00:10 .
drwxr-xr-x 14 anton anton 4096 Mar 28 00:09 ..
drwxr-xr-x  2 anton  1500 4096 Mar 28 00:10 .cm
drwxr-xr-x  3 anton  1500 4096 Mar 28 00:49 mlperf.closed.image-classification.velociti.tensorrt.resnet.multistream.performance

$ tree $CK_EXPERIMENTS_DIR
/data/anton/tensorrt-experiments
└── mlperf.closed.image-classification.velociti.tensorrt.resnet.multistream.performance
    ├── ckp-0cc49387454691a5.0001.json
    ├── ckp-0cc49387454691a5.features_flat.json
    ├── ckp-0cc49387454691a5.features.json
    ├── ckp-0cc49387454691a5.flat.json
    ├── ckp-3368d49d0824b41e.0001.json
    ├── ckp-3368d49d0824b41e.features_flat.json
    ├── ckp-3368d49d0824b41e.features.json
    ├── ckp-3368d49d0824b41e.flat.json
    ├── ckp-89accfd6c6f3fd9e.0001.json
    ├── ckp-89accfd6c6f3fd9e.features_flat.json
    ├── ckp-89accfd6c6f3fd9e.features.json
    ├── ckp-89accfd6c6f3fd9e.flat.json
    ├── ckp-c57a441db2d845f0.0001.json
    ├── ckp-c57a441db2d845f0.features_flat.json
    ├── ckp-c57a441db2d845f0.features.json
    ├── ckp-c57a441db2d845f0.flat.json
    ├── desc.json
    └── pipeline.json
```

Here's a quick-and-cheap way to ascertain that 31 samples per query was the optimum number of streams:
```bash
$ cd $CK_EXPERIMENTS_DIR/*.performance && grep "Result is\"" -RH -A2
ckp-89accfd6c6f3fd9e.0001.json:          "Result is": "VALID",
ckp-89accfd6c6f3fd9e.0001.json-          "SUT name": "PySUT",
ckp-89accfd6c6f3fd9e.0001.json-          "Samples per query": "1",
--
ckp-3368d49d0824b41e.0001.json:          "Result is": "VALID",
ckp-3368d49d0824b41e.0001.json-          "SUT name": "PySUT",
ckp-3368d49d0824b41e.0001.json-          "Samples per query": "31",
--
ckp-0cc49387454691a5.0001.json:          "Result is": "VALID",
ckp-0cc49387454691a5.0001.json-          "SUT name": "PySUT",
ckp-0cc49387454691a5.0001.json-          "Samples per query": "30",
--
ckp-c57a441db2d845f0.0001.json:          "Result is": "INVALID",
ckp-c57a441db2d845f0.0001.json-          "SUT name": "PySUT",
ckp-c57a441db2d845f0.0001.json-          "Samples per query": "32",
```

But we can do much better than that!

<a name="analyze"></a>
## Analyze

### Copy the results to another machine for analysis

Once you have accumulated some experiment entries in `CK_EXPERIMENTS_DIR`, archive them e.g.:
```bash
$ cd $CK_EXPERIMENTS_DIR
$ zip -rv mlperf.closed.image-classification.velociti.tensorrt.zip {.cm,*}
```
and copy the resulting archive to a machine where you would like to analyze them.

On that machine, create a new repository with a placeholder for experiment entries:
```bash
$ ck add repo:mlperf.closed.image-classification.velociti.tensorrt --quiet
$ ck add mlperf.closed.image-classification.velociti.tensorrt:experiment:dummy --common_func
$ ck rm  mlperf.closed.image-classification.velociti.tensorrt:experiment:dummy --force
```

Finally, extract the archived results into the new repository:
```bash
$ unzip mlperf.closed.image-classification.velociti.tensorrt.zip \
-d `ck find repo:mlperf.closed.image-classification.velociti.tensorrt`/experiment
Archive:  mlperf.closed.image-classification.velociti.tensorrt.zip
  inflating: /home/anton/CK_REPOS/mlperf.closed.image-classification.velociti.tensorrt/experiment/.cm/alias-u-892d289465870473
 extracting: /home/anton/CK_REPOS/mlperf.closed.image-classification.velociti.tensorrt/experiment/.cm/alias-a-mlperf.closed.image-classification.velociti.tensorrt.resnet.multistream.performance
   creating: /home/anton/CK_REPOS/mlperf.closed.image-classification.velociti.tensorrt/experiment/mlperf.closed.image-classification.velociti.tensorrt.resnet.multistream.performance/
  inflating: /home/anton/CK_REPOS/mlperf.closed.image-classification.velociti.tensorrt/experiment/mlperf.closed.image-classification.velociti.tensorrt.resnet.multistream.performance/ckp-3368d49d0824b41e.features.json
...
```

### Convert the results into the submission format

```bash
$ ck run ck-mlperf:program:dump-repo-to-submission \
--env.CK_MLPERF_SUBMISSION_REPO=mlperf.closed.image-classification.velociti.tensorrt \
--env.CK_MLPERF_SUBMISSION_ROOT=$HOME/mlperf.closed.image-classification.velociti.tensorrt-submission
```
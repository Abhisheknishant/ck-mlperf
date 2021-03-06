#
# Copyright (c) 2018 cTuning foundation.
# See CK COPYRIGHT.txt for copyright details.
#
# SPDX-License-Identifier: BSD-3-Clause.
# See CK LICENSE.txt for licensing details.
#

# import sys
import os
import json
import numpy as np
import time
import onnxruntime as rt


CUR_DIR = os.getcwd()

## Model properties:
#
MODEL_PATH = os.environ['CK_ENV_ONNX_MODEL_ONNX_FILEPATH']
MODEL_ROOT_PATH = os.environ['CK_ENV_ONNX_MODEL_ROOT']
MODEL_NAME = os.environ['CK_ENV_ONNX_MODEL_NAME']
MODEL_FILE = os.environ['CK_ENV_ONNX_MODEL_ONNX_FILENAME']
LABELS_PATH = os.path.join(MODEL_ROOT_PATH, os.environ['CK_ENV_ONNX_MODEL_CLASSES_LABELS'])
INPUT_LAYER_NAME = os.environ['CK_ENV_ONNX_MODEL_INPUT_LAYER_NAME']
OUTPUT_LAYER_BBOXES = os.environ['CK_ENV_ONNX_MODEL_OUTPUT_LAYER_BBOXES']
OUTPUT_LAYER_LABELS = os.environ['CK_ENV_ONNX_MODEL_OUTPUT_LAYER_LABELS']
OUTPUT_LAYER_SCORES = os.environ['CK_ENV_ONNX_MODEL_OUTPUT_LAYER_SCORES']
MODEL_DATA_LAYOUT = os.environ['ML_MODEL_DATA_LAYOUT']
MODEL_IMAGE_HEIGHT = int(os.environ['CK_ENV_ONNX_MODEL_IMAGE_HEIGHT'])
MODEL_IMAGE_WIDTH = int(os.environ['CK_ENV_ONNX_MODEL_IMAGE_WIDTH'])
MODEL_SKIPPED_CLASSES = os.getenv("CK_ENV_ONNX_MODEL_SKIPS_ORIGINAL_DATASET_CLASSES", None)

if (MODEL_SKIPPED_CLASSES):
    SKIPPED_CLASSES = [int(x) for x in MODEL_SKIPPED_CLASSES.split(",")]
else:
    SKIPPED_CLASSES = None

## Image normalization:
#
# special normalization mode used in https://github.com/mlperf/inference/blob/master/cloud/image_classification/python/dataset.py
#
GUENTHER_NORM = os.getenv("CK_GUENTHER_NORM") in ('YES', 'yes', 'ON', 'on', '1')
# or
#
MODEL_NORMALIZE_DATA = os.getenv("CK_ENV_ONNX_MODEL_NORMALIZE_DATA") in ('YES', 'yes', 'ON', 'on', '1')
SUBTRACT_MEAN = os.getenv("CK_SUBTRACT_MEAN") in ('YES', 'yes', 'ON', 'on', '1')
USE_MODEL_MEAN = os.getenv("CK_USE_MODEL_MEAN") in ('YES', 'yes', 'ON', 'on', '1')
MODEL_MEAN_VALUE = np.array([0, 0, 0], dtype=np.float32)  # to be populated

## Input image properties:
#
IMAGE_DIR = os.getenv('CK_ENV_DATASET_OBJ_DETECTION_PREPROCESSED_DIR')
IMAGE_LIST_FILE_NAME = os.getenv('CK_ENV_DATASET_OBJ_DETECTION_PREPROCESSED_SUBSET_FOF')
IMAGE_LIST_FILE = os.path.join(IMAGE_DIR, IMAGE_LIST_FILE_NAME)


DATASET_TYPE = os.getenv("CK_ENV_DATASET_TYPE")

# Program parameters
## Processing in batches:
#
BATCH_SIZE = int(os.getenv('CK_BATCH_SIZE', 1))
BATCH_COUNT = int(os.getenv('CK_BATCH_COUNT', 1))
IMAGE_COUNT = int(os.getenv('CK_BATCH_COUNT', 1))
SKIP_IMAGES = int(os.getenv('CK_SKIP_IMAGES', 0))
SCORE_THRESHOLD = float(os.getenv('CK_DETECTION_THRESHOLD', 0.3))
DETECTIONS_OUT_DIR = os.path.join(CUR_DIR, os.environ['CK_DETECTIONS_OUT_DIR'])
ANNOTATIONS_OUT_DIR = os.path.join(CUR_DIR, os.environ['CK_ANNOTATIONS_OUT_DIR'])
RESULTS_OUT_DIR = os.path.join(CUR_DIR, os.environ['CK_RESULTS_OUT_DIR'])
FULL_REPORT = os.getenv('CK_SILENT_MODE') == 'NO'
SKIP_DETECTION = os.getenv('CK_SKIP_DETECTION') == 'YES'
TIMER_JSON = 'tmp-ck-timer.json'
ENV_JSON = 'env.json'
CPU_THREADS = int(os.getenv('CK_HOST_CPU_NUMBER_OF_PROCESSORS',0))
RESULTS_DIR = os.getenv('CK_RESULTS_DIR')


## Writing the results out:
#
FULL_REPORT = os.getenv('CK_SILENT_MODE', '0') in ('NO', 'no', 'OFF', 'off', '0')

def load_labels(labels_filepath):
    my_labels = []
    input_file = open(labels_filepath, 'r')
    for l in input_file:
        my_labels.append(l.strip())
    return my_labels


def load_preprocessed_file(image_file):
    img = np.fromfile(image_file, np.uint8)
    img = img.reshape((MODEL_IMAGE_HEIGHT, MODEL_IMAGE_WIDTH, 3))
    img = img.astype(np.float32)

    if GUENTHER_NORM and (MODEL_NAME == "MLPerf SSD-Resnet"):
        mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
        img = img / 255. - mean
        img = img / std
    else:
        # Normalize
        if MODEL_NORMALIZE_DATA:
            img = img/127.5 - 1.0

        # Subtract mean value
        if SUBTRACT_MEAN:
            if USE_MODEL_MEAN:
                img = img - MODEL_MEAN_VALUE
            else:
                img = img - np.mean(img)

    # Add img to batch
    nhwc_data = img

    nhwc_data = np.expand_dims(nhwc_data, axis=0)

    if MODEL_DATA_LAYOUT == 'NHWC':
        # print(nhwc_data.shape)
        return nhwc_data
    else:
        nchw_data = nhwc_data.transpose(0,3,1,2)
        # print(nchw_data.shape)
        return nchw_data

def detect():
    global INPUT_LAYER_NAME
    OPENME = {}

    setup_time_begin = time.time()

    # Load preprocessed image filenames:
    with open(IMAGE_LIST_FILE, 'r') as f:
        image_list = [s.strip() for s in f]
    
    images_total_count = len(image_list)
    first_index = SKIP_IMAGES
    last_index = BATCH_COUNT * BATCH_SIZE + first_index

    if first_index > images_total_count or last_index > images_total_count:
        print('********************************************')
        print('')
        print('DATASET SIZE EXCEEDED !!!')
        print('Dataset size  : {}'.format(images_total_count))
        print('CK_SKIP_IMAGES: {}'.format(SKIP_IMAGES))
        print('CK_BATCH_COUNT: {}'.format(BATCH_COUNT))
        print('CK_BATCH_SIZE : {}'.format(BATCH_SIZE))
        print('')
        print('********************************************')

    image_list = image_list[SKIP_IMAGES: BATCH_COUNT * BATCH_SIZE + SKIP_IMAGES]

    # Local list of processed files
    with open(IMAGE_LIST_FILE_NAME, 'w') as f:
        for line in image_list:
            f.write('{}\n'.format(line))

    # Load the ONNX model from file
    sess_options = rt.SessionOptions()
    # sess_options.session_log_verbosity_level = 0
    if CPU_THREADS > 0:
        sess_options.enable_sequential_execution = False
        sess_options.session_thread_pool_size = CPU_THREADS
    graph_load_time_begin = time.time()
    sess = rt.InferenceSession(MODEL_PATH, sess_options)
    graph_load_time = time.time() - graph_load_time_begin

    input_layer_names = [x.name for x in sess.get_inputs()]     # FIXME: check that INPUT_LAYER_NAME belongs to this list
    INPUT_LAYER_NAME = INPUT_LAYER_NAME or input_layer_names[0]

    output_layer_names = [x.name for x in sess.get_outputs()]    # FIXME: check that OUTPUT_LAYER_NAME belongs to this list

    model_input_shape = sess.get_inputs()[0].shape
    model_input_type  = sess.get_inputs()[0].type
    model_input_type  = np.uint8 if model_input_type == 'tensor(uint8)' else np.float32     # FIXME: there must be a more humane way!

        # a more portable way to detect the number of classes
    for output in sess.get_outputs():
        if output.name == OUTPUT_LAYER_LABELS:
            model_classes = output.shape[1]

    labels = load_labels(LABELS_PATH)
    #bg_class_offset = model_classes-len(labels)  # 1 means the labels represent classes 1..1000 and the background class 0 has to be skipped
    bg_class_offset = 1

    if MODEL_DATA_LAYOUT == 'NHWC':
        (samples, height, width, channels) = model_input_shape
    else:
        (samples, channels, height, width) = model_input_shape

    print("Data layout: {}".format(MODEL_DATA_LAYOUT) )
    print("Input layers: {}".format(input_layer_names))
    print("Output layers: {}".format(output_layer_names))
    print("Input layer name: " + INPUT_LAYER_NAME)
    print("Expected input shape: {}".format(model_input_shape))
    print("Expected input type: {}".format(model_input_type))
    print("Output layer names: " + ", ".join([OUTPUT_LAYER_BBOXES, OUTPUT_LAYER_LABELS, OUTPUT_LAYER_SCORES]))
    print("Data normalization: {}".format(MODEL_NORMALIZE_DATA))
    print("Background/unlabelled classes to skip: {}".format(bg_class_offset))
    print("")

    setup_time = time.time() - setup_time_begin

    # Run batched mode
    test_time_begin = time.time()
    total_load_time = 0
    total_detection_time = 0
    first_detection_time = 0
    images_loaded = 0

    ## Due to error in ONNX Resnet34 model
    class_map = None
    if (SKIPPED_CLASSES):
        class_map = []
        for i in range(len(labels) + bg_class_offset):
            if i not in SKIPPED_CLASSES:
                class_map.append(i)

    for image_index in range(BATCH_COUNT):

        if FULL_REPORT or (image_index % 10 == 0):
            print("\nBatch {} of {}".format(image_index + 1, BATCH_COUNT))

        begin_time = time.time()
        file_name, width, height = image_list[image_index].split(";")
        width = float(width)
        height = float(height)
        img_file = os.path.join(IMAGE_DIR, file_name)
        batch_data = load_preprocessed_file(img_file).astype(model_input_type)

        load_time = time.time() - begin_time
        total_load_time += load_time
        images_loaded += 1
        if FULL_REPORT:
            print("Batch loaded in %fs" % load_time)

        # Detect batch
        begin_time = time.time()
        run_options = rt.RunOptions()
        # run_options.run_log_verbosity_level = 0
        batch_results = sess.run([OUTPUT_LAYER_BBOXES, OUTPUT_LAYER_LABELS, OUTPUT_LAYER_SCORES], {INPUT_LAYER_NAME: batch_data}, run_options)
        detection_time = time.time() - begin_time
        if FULL_REPORT:
            print("Batch classified in %fs" % detection_time)

        total_detection_time += detection_time
        # Remember first batch prediction time
        if image_index == 0:
            first_detection_time = detection_time

        # Process results
        # res_name = file.with.some.name.ext -> file.with.some.name.txt
        res_name = ".".join(file_name.split(".")[:-1]) + ".txt"
        res_file = os.path.join(DETECTIONS_OUT_DIR, res_name)
        with open(res_file, 'w') as f:
            f.write('{:d} {:d}\n'.format(int(width), int(height)))
            for i in range(len(batch_results[2][0])):
                score = batch_results[2][0][i]
                if score > SCORE_THRESHOLD:
                    if class_map:
                        class_num = class_map[batch_results[1][0][i]]
                    else:
                        class_num = batch_results[1][0][i] + bg_class_offset
                    class_name = labels[class_num - bg_class_offset]
                    box = batch_results[0][0][i]
                    x1 = box[0] * width
                    y1 = box[1] * height
                    x2 = box[2] * width
                    y2 = box[3] * height
                    f.write('{:.2f} {:.2f} {:.2f} {:.2f} {:.3f} {} {}\n'.format(x1,
                                                                                y1,
                                                                                x2,
                                                                                y2,
                                                                                score,
                                                                                class_num,
                                                                                class_name
                                                                                )
                            )

    test_time = time.time() - test_time_begin

    if BATCH_COUNT > 1:
        avg_detection_time = (total_detection_time - first_detection_time) / (images_loaded - BATCH_SIZE)
    else:
        avg_detection_time = total_detection_time / images_loaded

    avg_load_time = total_load_time / images_loaded

    # Save processed images ids list to be able to run
    # evaluation without repeating detections (CK_SKIP_DETECTION=YES)
    # with open(IMAGE_LIST_FILE, 'w') as f:
    #    f.write(json.dumps(processed_image_ids))

    OPENME['setup_time_s'] = setup_time
    OPENME['test_time_s'] = test_time
    OPENME['load_images_time_total_s'] = total_load_time
    OPENME['load_images_time_avg_s'] = avg_load_time
    OPENME['prediction_time_total_s'] = total_detection_time
    OPENME['prediction_time_avg_s'] = avg_detection_time
    OPENME['avg_time_ms'] = avg_detection_time * 1000
    OPENME['avg_fps'] = 1.0 / avg_detection_time if avg_detection_time > 0 else 0

    run_time_state = {"run_time_state": OPENME}

    with open(TIMER_JSON, 'w') as o:
        json.dump(run_time_state, o, indent=2, sort_keys=True)

    return


def main():

    # Print settings
    print("Model name: " + MODEL_NAME)
    print("Model file: " + MODEL_FILE)

    print("Dataset images: " + IMAGE_DIR)
    print("Dataset annotations: " + ANNOTATIONS_OUT_DIR)
    print("Dataset type: " + DATASET_TYPE)

    print('Image count: {}'.format(IMAGE_COUNT))
    print('Results directory: {}'.format(RESULTS_OUT_DIR))
    print("Temporary annotations directory: " + ANNOTATIONS_OUT_DIR)
    print("Detections directory: " + DETECTIONS_OUT_DIR)

    # Run detection if needed
    if SKIP_DETECTION:
        print('\nSkip detection, evaluate previous results')
    else:
        detect()


if __name__ == '__main__':
    main()

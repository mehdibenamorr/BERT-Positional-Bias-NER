#!/usr/bin/env bash
# -*- coding: utf-8 -*-

#Training ARGS
SEED=23456
TRAIN_BATCH_SIZE=5
EVAL_BATCH_SIZE=12
#MAX_LENGTH=128
SEQ_LENTGH=max
OPTIMIZER=adamw_hf
LR_SCHEDULE=linear
LR=5e-5
MAX_EPOCH=5

#Script ARGS
MODEL=bert-base-uncased
DATASET=$1
NBRUNS=5
PADDING=max_length
PADDING_SIDE=$2


OUTPUT_DIR=/data/.position_bias
DEV_SHUFFLE=0.5

REPO=/data/p-22-ner-position-bias
export PYTHONPATH="$PYTHONPATH:$REPO"


python ${REPO}/experiments/bert_position_bias.py \
--output_dir=${OUTPUT_DIR} \
--dataset=${DATASET} \
--seq_length=${SEQ_LENTGH} \
--padding=${PADDING} \
--nbruns=${NBRUNS} \
--seed=${SEED} \
--per_device_train_batch_size ${TRAIN_BATCH_SIZE} \
--per_device_eval_batch_size ${EVAL_BATCH_SIZE} \
--optim ${OPTIMIZER} \
--learning_rate ${LR} \
--lr_scheduler_type ${LR_SCHEDULE} \
--num_train_epochs ${MAX_EPOCH} \
--shuffle \
--truncation


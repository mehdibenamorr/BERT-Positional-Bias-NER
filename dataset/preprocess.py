#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# file: preprocess.py
#
import conllu

from utils import set_random_seed

set_random_seed(23456)
import argparse
import os
import random
from tqdm import tqdm
import numpy as np


def tags_to_spans(tokens, tags):
    """
    Desc:
        get from token_level labels to list of entities,
        it does not matter tagging scheme is BMES or BIO or IOBES
    Returns:
        a list of entities
        [[token1],[token2,token3],...],
        [[tag1],[tag2,tag3],...]
    """

    span_labels = []
    segmented_tokens = []
    segmented_labels = []
    last = "O"
    start = -1
    for i, tag in enumerate(tags):
        pos, _ = (None, "O") if tag == "O" else tag.split("-")
        if (pos == "S" or pos == "B" or tag == "O") and last != "O":
            span_labels.append((start, i - 1, last.split("-")[-1]))
            segmented_tokens.append(tokens[start:i])
            segmented_labels.append(tags[start:i])
        if pos == "B" or pos == "S" or last == "O":
            start = i
        if tag == "O" and last == "O":
            segmented_tokens.append([tokens[i]])
            segmented_labels.append([tags[i]])
        last = tag

    if tags[-1] != "O":
        span_labels.append((start, len(tags) - 1, tags[-1].split("-"[-1])))
        segmented_tokens.append(tokens[start:len(tags)])
        segmented_labels.append(tags[start:len(tags)])

    return segmented_tokens, segmented_labels


def shuffle_dataset(dataset, ratio=0.2):
    shuffled = dict()
    ids = dataset.keys()
    n = int(ratio * len(ids))
    to_shuffle = random.sample(ids, n) if ratio < 1.0 else ids
    for id, item in tqdm(dataset.items()):
        if id in to_shuffle:
            segmented_tokens, segmented_labels = tags_to_spans(item["tokens"], item["ner_tags"])
            indices = list(range(len(segmented_tokens)))
            random.shuffle(indices)
            shuffled_item = {"tokens": [], "ner_tags": []}
            for idx in indices:
                shuffled_item["tokens"] += segmented_tokens[idx]
                shuffled_item["ner_tags"] += segmented_labels[idx]
            shuffled.update({id: shuffled_item})
        else:
            shuffled.update({id: item})
    return shuffled


def read_data(filepath, format="iobes"):
    dataset = dict()
    if format == "conllu":
        with open(filepath, encoding="utf-8") as f:
            guid = 0
            tokenlist = list(conllu.parse_incr(f))
            for sent in tokenlist:
                if "sent_id" in sent.metadata:
                    idx = sent.metadata["sent_id"]
                else:
                    idx = guid
                dataset.update({str(idx): {
                    "tokens": [token["form"] for token in sent],
                    "pos_tags": [token["upos"] for token in sent],
                }
                })
                guid += 1
        return dataset, tokenlist
    else:
        with open(filepath, encoding="utf-8") as f:
            guid = 0
            tokens = []
            ner_tags = []
            lines = f.readlines()
            for line in lines:
                if line == "" or line == "\n":
                    if tokens:
                        dataset.update({str(guid): {
                            "tokens": tokens,
                            "ner_tags": ner_tags,
                        }
                        })
                        guid += 1
                        tokens = []
                        ner_tags = []
                else:
                    splits = line.split(" ")
                    tokens.append(splits[0])
                    ner_tags.append(splits[-1].rstrip())
        return dataset, None


def process_data(filepath, ratio=None):
    # The full dataset split (val, or test)
    dataset = read_data(filepath)
    # Shuffling of tokens
    shuffled = shuffle_dataset(dataset, ratio=ratio)
    save(shuffled, filename=filepath + ".shuffled")
    return shuffled


def trim_dataset(dataset, data_dir, format="iobes"):
    if format == "iobes":
        train_file = os.path.join(data_dir, dataset, "train.word.iobes")
        dev_file = os.path.join(data_dir, dataset, "dev.word.iobes")
        test_file = os.path.join(data_dir, dataset, "test.word.iobes")
    else:
        train_file = os.path.join(data_dir, dataset, f"{dataset}-ud-train.conllu")
        dev_file = os.path.join(data_dir, dataset, f"{dataset}-ud-dev.conllu")
        test_file = os.path.join(data_dir, dataset, f"{dataset}-ud-test.conllu")

    train, train_list = read_data(train_file, format=format)
    dev, dev_list = read_data(dev_file, format=format)
    test, test_list = read_data(test_file, format=format)

    sequence_lengths = [len(a["tokens"]) for i, a in train.items()] + [len(a["tokens"]) for i, a in dev.items()] + [
        len(a["tokens"]) for i, a in test.items()]
    ## select 25% - 75% of examples based on the sequence length distribution
    q1 = np.percentile(sequence_lengths, 15)
    q3 = np.percentile(sequence_lengths, 75)
    if format == "iobes":
        cut_train = {i: example for i, example in train.items() if
                     (len(example["tokens"]) <= q3 and len(example["tokens"]) >= q1)}
        save(cut_train, filename=train_file + ".cut", format=format)
        cut_test = {i: example for i, example in test.items() if
                    (len(example["tokens"]) <= q3 and len(example["tokens"]) >= q1)}
        save(cut_test, filename=test_file + ".cut")
        cut_dev = {i: example for i, example in dev.items() if
                   (len(example["tokens"]) <= q3 and len(example["tokens"]) >= q1)}
        save(cut_dev, filename=dev_file + ".cut")
        all_ = list(cut_train.values()) + list(cut_dev.values()) + list(cut_test.values())
        all_data = {str(i): example for i, example in enumerate(all_)}
    else:
        cut_train = [a for a in train_list if q1 <= len([b["form"] for b in a]) <= q3]
        save(cut_train, filename=train_file + ".cut",format=format)
        cut_test = [a for a in test_list if q1 <= len([b["form"] for b in a]) <= q3]
        save(cut_test, filename=test_file + ".cut",format=format)
        cut_dev = [a for a in dev_list if q1 <= len([b["form"] for b in a]) <= q3]
        save(cut_dev, filename=dev_file + ".cut",format=format)
        all_data = cut_train + cut_dev + cut_test
    all_file = train_file.replace("train", "all") + ".cut"
    save(all_data, all_file, format=format)


def save(data, filename, format="iobes"):
    if format == "iobes":
        with open(filename, "w") as file:
            for id, item in data.items():
                for i in range(len(item["tokens"])):
                    file.write(" ".join([item["tokens"][i], item["ner_tags"][i]]))
                    file.write("\n")
                file.write("\n")
    elif format == "conllu":
        with open(filename, "w") as file:
            file.writelines([a.serialize() + "\n" for a in data])


def processing_args() -> argparse.ArgumentParser:
    """
        return basic arg parser
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", type=str, help="dataset directory")
    parser.add_argument("--dataset", type=str, help="dataset to use",
                        choices=["en_conll03", "ontonotes5", "en_ewt", "tweebank"])
    parser.add_argument("--dev_shuffle",
                        default=0.5,
                        help="percentage of data samples to be shuffled in the validation set")
    parser.add_argument("--shuffle",
                        action="store_true",
                        help="percentage of data samples to be shuffled in the validation set")
    parser.add_argument("--duplicate",
                        action="store_true",
                        help="percentage of data samples to be shuffled in the validation set")
    parser.add_argument("--format", type=str, help="format of the dataset",
                        choices=["iobes", "conllu"])

    return parser


if __name__ == "__main__":
    parser = processing_args()
    args = parser.parse_args()

    # Shuffling experiment
    if args.shuffle:
        # ### Train dataset
        train_path = os.path.join(args.data_dir, args.dataset, "train.word.iobes")
        process_data(train_path, ratio=0.5)
        # ### Dev dataset
        print(args.data_dir)
        dev_path = os.path.join(args.data_dir, args.dataset, "dev.word.iobes")
        process_data(dev_path, ratio=0.5)
        ### Test dataset
        test_path = os.path.join(args.data_dir, args.dataset, "test.word.iobes")
        process_data(test_path, ratio=1)
    elif args.duplicate:
        trim_dataset(args.dataset, args.data_dir, format=args.format)

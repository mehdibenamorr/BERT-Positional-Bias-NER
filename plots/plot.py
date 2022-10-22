import pandas as pd
import numpy as np
import matplotlib
import pandas as pd
import wandb

from dataset.ner_dataset import NERDataset

matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from scipy.stats import spearmanr
import seaborn as sns
from scipy.stats import norm

api = wandb.Api()

# sns.set(style='ticks', palette='Set2')
# colors = ['#E69F00', '#56B4E9', '#F0E442', '#009E73', '#D55E00']
"""
1.5 columns (5,3.75) ; 1 column (3.54,2.65) ; 2 columns (7.25,5.43)
"""
style = {"figure.figsize": (5, 3.75),
         "figure.titlesize": 11,
         "legend.frameon": False,
         "legend.loc": 'upper right',
         "legend.fontsize": 11,
         "axes.labelsize": 11,
         "axes.titlesize": 11,
         "savefig.bbox": 'tight',
         "savefig.pad_inches": 0.05,
         "savefig.dpi": 300,
         "xtick.direction": 'in',
         "xtick.labelsize": 11,
         "xtick.major.size": 4,
         "xtick.major.width": 2,
         "xtick.minor.size": 2,
         "xtick.minor.width": 1,
         "xtick.minor.visible": True,
         "xtick.top": False,
         "xtick.bottom": True,
         "ytick.direction": 'in',
         "ytick.labelsize": 11,
         "ytick.major.size": 4,
         "ytick.major.width": 2,
         "ytick.minor.size": 2,
         "ytick.minor.width": 1,
         "ytick.minor.visible": True,
         "ytick.right": False,
         "ytick.left": True
         }
sns.set(context='paper', style='white', font_scale=1.5, color_codes=True, rc=style)

sns.set_theme(style="ticks")
plots_path = 'plots/files/'


# Datasets
def dataset_plot():
    conll03 = NERDataset(dataset="conll03")
    ontonotes5 = NERDataset(dataset="ontonotes5")

    conll03_seq = pd.DataFrame(conll03.sequence_lengths, columns=["seq_lengths"])
    f, ax_hist = plt.subplots(1, figsize=(3.54, 2.65))
    sns.histplot(conll03_seq["seq_lengths"], ax=ax_hist,
                 edgecolor='black')

    ax_hist.set(xlabel='Sequence lengths', ylabel='Count')

    plt.legend()
    f.savefig(plots_path + 'conll03_seq_lengths.pdf')

    ontonotes5_seq = pd.DataFrame(ontonotes5.sequence_lengths, columns=["seq_lengths"])
    f, ax_hist = plt.subplots(1, figsize=(3.54, 2.65))
    sns.histplot(ontonotes5_seq["seq_lengths"], ax=ax_hist,
                 edgecolor='black')

    ax_hist.set(xlabel='Sequence lengths', ylabel='Count')

    plt.legend()
    f.savefig(plots_path + 'ontonotes5_seq_lengths.pdf')

    df = pd.DataFrame([(x,"conll03") for x in conll03.sequence_lengths] + [(x,"ontonotes5") for x in ontonotes5.sequence_lengths],
                      columns=["seq_lengths", "dataset"])

    f, ax = plt.subplots(figsize=(7.25, 2.43))

    # Plot the orbital period with horizontal boxes
    sns.boxplot(x="seq_lengths", y="dataset", data=df,
                width=.3, palette="vlag", whis=[0, 100])

    # Tweak the visual presentation
    ax.set(ylabel="",xlabel='Sequence lengths')
    f.savefig(plots_path + 'seq_lengths.pdf')
    # Class distribution


def bias_experiment(experiment="bert-position-bias-conll03", dataset="conll03"):
    NERDataset(dataset=dataset)
    entity = "mehdi-benamor-uni-passau-de"  # set to your entity and project
    runs = api.runs(entity + "/" + experiment)


    # Per Class distribution f1 score for max and min
    # api.runs(
    #     path="my_entity/my_project",
    #     filters={"display_name": {"$regex": "^foo.*"}}
    # )

    summary_list, config_list, name_list = [], [], []
    for run in runs:
        # .summary contains the output keys/values for metrics like accuracy.
        #  We call ._json_dict to omit large files
        if run.state == "finished":
            summary_list.append(run.summary._json_dict)
            run.history()
            # .config contains the hyperparameters.
            #  We remove special values that start with _.
            config_list.append(
                {k: v for k, v in run.config.items()
                 if not k.startswith('_')})

            # .name is the human-readable name of the run.
            name_list.append(run.name)

    runs_df = pd.DataFrame({
        "summary": summary_list,
        "config": config_list,
        "name": name_list
    })

    runs_df.to_csv("project.csv")


if __name__ == "__main__":
    dataset_plot()
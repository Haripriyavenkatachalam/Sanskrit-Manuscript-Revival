# -*- coding: utf-8 -*-
"""Sanskrit_with_Vocabulary_Training_and_Perplexity.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1ovR8oOirp1vZLWd7M8_CINoKdrDBHdl6

Open a new or existing Colab notebook.
Go to the "Runtime" menu at the top.
Select "Change runtime type."
Ensure that "Hardware accelerator" is set to "GPU."

Run pip install accelerate -U in a cell
In the top menu click Runtime → Restart Runtime
Do not rerun any cells with !pip install in them
Rerun all the other code cells and you should be good to go!
"""

!pip install transformers datasets evaluate

!pip install accelerate -U

!huggingface-cli login

!git config --global credential.helper store

from datasets import load_dataset

san_data = load_dataset("sanskrit_classic")
san_data

dataset = san_data["train"]
dataset[:10]

with open('sa.txt', 'w') as sa_file:
    for sanskrit_text in dataset['text']:
        sa_file.write(sanskrit_text)

print("Sanskrit text has been written to sa.txt")

# Read and print the first 5 lines of sa.txt
with open('sa.txt', 'r') as sa_file:
    first_five_lines = [next(sa_file) for _ in range(5)]

# Print the first 5 lines
for line_number, line in enumerate(first_five_lines, start=1):
    print(f"Line {line_number}: {line}")

from pathlib import Path
from tokenizers import ByteLevelBPETokenizer

# Specify the path to your Sanskrit text file
sanskrit_text_file = "sa.txt"

# Check if the file exists
if Path(sanskrit_text_file).exists():
    # Initialize a ByteLevelBPETokenizer
    tokenizer = ByteLevelBPETokenizer()

    # Customize training
    tokenizer.train(files=[sanskrit_text_file], vocab_size=52_000, min_frequency=2, special_tokens=[
        "<s>",
        "<pad>",
        "</s>",
        "<unk>",
        "<mask>",
    ])

!mkdir MySan2

tokenizer.save_model("MySan2")

from tokenizers.implementations import ByteLevelBPETokenizer
from tokenizers.processors import BertProcessing


tokenizer = ByteLevelBPETokenizer(
    "./MySan2/vocab.json",
    "./MySan2/merges.txt",
)

tokenizer._tokenizer.post_processor = BertProcessing(
    ("</s>", tokenizer.token_to_id("</s>")),
    ("<s>", tokenizer.token_to_id("<s>")),
)
tokenizer.enable_truncation(max_length=512)

tokenizer.encode("तत्र सत्यस्य परमं निधानं यः न प्रियः ।")

tokenizer.encode("तत्र सत्यस्य परमं निधानं यः न प्रियः ।").tokens

from transformers import RobertaConfig

config = RobertaConfig(
    vocab_size=52_000,
    max_position_embeddings=514,
    num_attention_heads=12,
    num_hidden_layers=6,
    type_vocab_size=1,
)

from transformers import RobertaTokenizerFast

tokenizer = RobertaTokenizerFast.from_pretrained("./MySan2", max_len=512)

from transformers import RobertaForMaskedLM

model = RobertaForMaskedLM(config=config)

model.num_parameters()

from transformers import LineByLineTextDataset

line_dataset = LineByLineTextDataset(
    tokenizer=tokenizer,
    file_path="sa.txt",
    block_size=128,
)

from torch.utils.data import random_split

#Define the total size of the dataset
total_size = len(line_dataset)

#Define the size of the training and validation datasets
train_size = int(0.8 * total_size)
val_size = total_size - train_size

#Split the dataset into training and validation datasets
train_dataset, val_dataset = random_split(line_dataset, [train_size, val_size])

from transformers import DataCollatorForLanguageModeling

data_collator = DataCollatorForLanguageModeling(
    tokenizer=tokenizer, mlm=True, mlm_probability=0.15
)

from transformers import Trainer, TrainingArguments
import math

training_args = TrainingArguments(
    output_dir="./MySan2",
    overwrite_output_dir=True,
    num_train_epochs=1,
    save_steps=10_000,
    save_total_limit=2,
    prediction_loss_only=True,
    evaluation_strategy="steps",  # Evaluate every specified number of steps
    eval_steps=2500,  # Evaluate every 2500 steps (less than that takes too much time)
)

trainer = Trainer(
    model=model,
    args=training_args,
    data_collator=data_collator,
    train_dataset=train_dataset,
    eval_dataset=val_dataset,  # Include validation dataset
)

def compute_metrics(pred):
    # Compute perplexity as the exponential of the loss since it's MLM
    loss = pred.loss
    perplexity = math.exp(loss)
    return {"perplexity": perplexity}

trainer.compute_metrics = compute_metrics  # Set the custom metrics function

#Start training
trainer.train()

evaluation_results = trainer.evaluate()

print("Perplexity:", evaluation_results["eval_loss"])

trainer.save_model("./MySan2")

tokenizer.push_to_hub("my-mini-project-model")

from transformers import AutoModel

model = AutoModel.from_pretrained("./MySan2")
model.push_to_hub("my-mini-project-model")

from transformers import pipeline

fill_mask = pipeline(
    "fill-mask",
    model="./MySan2",
    tokenizer="./MySan2"
)

#सः वदति – “अद्य वर्षान्तस्य समारोहम् आगच्छतु”

fill_mask("<mask> वदति – “अद्य वर्षान्तस्य समारोहम् आगच्छतु”")
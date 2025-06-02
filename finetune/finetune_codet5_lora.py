# finetune/finetune_codet5_lora.py

"""
Fine-tune CodeT5 using LoRA (8-bit) on the prepared JSONL dataset.
Since you’re on Transformers v4.52.4 (where `evaluation_strategy` was removed),
we now replace it with `eval_strategy`.
"""

import json
import torch
import argparse
from datasets import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSeq2SeqLM,
    TrainingArguments,
    Trainer,
)
from peft import LoraConfig, get_peft_model


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="../data/train.jsonl")
    args = parser.parse_args()

    # 1) Load JSONL dataset --------------------------------------------------
    raw = [json.loads(line) for line in open(args.data, encoding="utf-8")]
    ds = Dataset.from_list(raw).shuffle(seed=42).train_test_split(test_size=0.1)

    # 2) Initialize tokenizer + base model in 8-bit mode ----------------------
    tokenizer = AutoTokenizer.from_pretrained("Salesforce/codet5-base")
    model = AutoModelForSeq2SeqLM.from_pretrained(
        "Salesforce/codet5-base",
        load_in_8bit=True,
        device_map="auto"
    )

    # 3) Apply LoRA configuration ---------------------------------------------
    lora_cfg = LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=["q", "v", "k", "o"],
        lora_dropout=0.05
    )
    model = get_peft_model(model, lora_cfg)

    # 4) Tokenization transform ------------------------------------------------
    def preprocess(batch):
        inputs = tokenizer(
            batch["code"], truncation=True, padding="max_length", max_length=512
        )
        outputs = tokenizer(
            batch["review"], truncation=True, padding="max_length", max_length=128
        )
        inputs["labels"] = outputs["input_ids"]
        return inputs

    ds_tok = ds.map(preprocess, batched=True, remove_columns=["code", "review"])

    # 5) Training arguments (using `eval_strategy` for v4.52.4+) ---------------
    args_tr = TrainingArguments(
        output_dir="../models/codet5-lora",
        num_train_epochs=3,
        per_device_train_batch_size=4,
        per_device_eval_batch_size=4,
        gradient_accumulation_steps=4,
        learning_rate=3e-5,
        weight_decay=0.01,
        eval_strategy="epoch",       # replaces evaluation_strategy="epoch"
        save_strategy="epoch",
        logging_steps=50,
        bf16=torch.cuda.is_available(),
        report_to="none",
    )

    # 6) Initialize Trainer (with eval dataset) --------------------------------
    trainer = Trainer(
        model=model,
        args=args_tr,
        train_dataset=ds_tok["train"],
        eval_dataset=ds_tok["test"],
        tokenizer=tokenizer
    )

    # 7) Launch fine-tuning ---------------------------------------------------
    trainer.train()

    # 8) Save the fine-tuned model -------------------------------------------
    model.save_pretrained("../models/codet5-lora")
    tokenizer.save_pretrained("../models/codet5-lora")
    print("✅  Fine-tuned model saved to ../models/codet5-lora")


if __name__ == "__main__":
    main()

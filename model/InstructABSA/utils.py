import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import torch
from torch.utils.data import DataLoader
from torch.nn.utils.rnn import pad_sequence
from tqdm import tqdm
from transformers import (
    DataCollatorForSeq2Seq, AutoTokenizer, AutoModelForSeq2SeqLM,
    Seq2SeqTrainingArguments, Trainer, Seq2SeqTrainer
)
from torch.backends import mps

class T5Generator:
    def __init__(self, model_checkpoint: str, max_new_tokens: int = 128):
        # Load tokenizer & model
        self.tokenizer = AutoTokenizer.from_pretrained(model_checkpoint)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_checkpoint)
        self.data_collator = DataCollatorForSeq2Seq(self.tokenizer)
        self.device = 'cuda' if torch.cuda.is_available() else ('mps' if mps.is_available() else 'cpu')

        # number of new tokens to generate beyond input length
        self.max_new_tokens = max_new_tokens

    def tokenize_function_inputs(self, sample):
        """
        Tokenize input text dynamically, capping at model_max_length.
        """
        # 1. Tokenize to count
        tokens = self.tokenizer.tokenize(sample['text'])
        model_max = self.tokenizer.model_max_length
        capped = tokens[:model_max]  # nếu vượt model_max, cắt xuống
        prompt_str = self.tokenizer.convert_tokens_to_string(capped)

        # 2. Final tokenization (will add special tokens automatically)
        inputs = self.tokenizer(prompt_str, return_tensors=None, add_special_tokens=True)

        # 3. Tokenize labels (targets) with truncation guard
        labels = self.tokenizer(
            sample['labels'],
            truncation=True,
            max_length=model_max,
            return_tensors=None
        )
        inputs['labels'] = labels['input_ids']
        return inputs

    def train(self, tokenized_datasets, **kwargs):
        """
        Train the generative model.
        """
        #Set training arguments
        args = Seq2SeqTrainingArguments(
            **kwargs
        )

        # Define trainer object
        trainer = Seq2SeqTrainer(
            self.model,
            args,
            train_dataset=tokenized_datasets["train"],
            eval_dataset=tokenized_datasets["validation"] if tokenized_datasets.get("validation") is not None else None,
            tokenizer=self.tokenizer,
            data_collator=self.data_collator,
        )
        print("Trainer device:", trainer.args.device)

        # Finetune the model
        torch.cuda.empty_cache()
        print('\nModel training started ....')
        trainer.train()

        # Save best model
        trainer.save_model()
        return trainer

    def get_labels(self, tokenized_dataset, batch_size: int = 4, sample_set: str = 'train'):
        """
        Generate predictions where output length = input_length + max_new_tokens.
        """

        def collate_fn(batch):
            seqs = [torch.tensor(ex['input_ids']) for ex in batch]
            return pad_sequence(seqs, batch_first=True, padding_value=self.tokenizer.pad_token_id)

        loader = DataLoader(tokenized_dataset[sample_set], batch_size=batch_size, collate_fn=collate_fn)
        self.model.to(self.device)
        self.model.eval()
        preds = []
        with torch.no_grad():
            for batch in tqdm(loader, desc='Generating'):
                batch = batch.to(self.device)
                # dynamic max_length = current prompt length + max_new_tokens
                prompt_len = batch.shape[1]
                max_len = prompt_len + self.max_new_tokens
                outputs = self.model.generate(
                    batch,
                    max_length=max_len,
                    num_beams=4,
                    early_stopping=True,
                    use_cache=True
                )
                preds.extend(self.tokenizer.batch_decode(outputs, skip_special_tokens=True))
        return preds

    def get_metrics(self, y_true, y_pred, is_triplet_extraction=False):
        tp = total_pred = total_gt = 0
        for gt, pred in zip(y_true, y_pred):
            gt_items = [x.strip() for x in gt.split(',') if x.strip()]
            pred_items = [x.strip() for x in pred.split(',') if x.strip()]
            total_pred += len(pred_items)
            total_gt += len(gt_items)
            for g in gt_items:
                for p in pred_items:
                    if not is_triplet_extraction:
                        if p in g or g in p:
                            tp += 1
                            break
                    else:
                        g_parts, p_parts = g.split(':'), p.split(':')
                        if len(g_parts) >= 3 and len(p_parts) >= 3:
                            if (p_parts[0] in g_parts[0]
                                    and p_parts[1] in g_parts[1]
                                    and p_parts[2] == g_parts[2]):
                                tp += 1
                                break
        precision = tp / total_pred if total_pred else 0
        recall = tp / total_gt if total_gt else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0
        return precision, recall, f1

class T5Classifier:
    def __init__(self, model_checkpoint):
        self.tokenizer = AutoTokenizer.from_pretrained(model_checkpoint, force_download = True)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_checkpoint, force_download = True)
        self.data_collator = DataCollatorForSeq2Seq(self.tokenizer)
        self.device = 'cuda' if torch.cuda.is_available() else ('mps' if mps.is_available() else 'cpu')

    def tokenize_function_inputs(self, sample):
        """
        Udf to tokenize the input dataset.
        """
        sample['input_ids'] = self.tokenizer(sample["text"], max_length = 512, truncation = True).input_ids
        sample['labels'] = self.tokenizer(sample["labels"], max_length = 64, truncation = True).input_ids
        return sample
        
    def train(self, tokenized_datasets, **kwargs):
        """
        Train the generative model.
        """

        # Set training arguments
        args = Seq2SeqTrainingArguments(
            **kwargs
            )

        # Define trainer object
        trainer = Trainer(
            self.model,
            args,
            train_dataset=tokenized_datasets["train"],
            eval_dataset=tokenized_datasets["validation"] if tokenized_datasets.get("validation") is not None else None,
            tokenizer=self.tokenizer, 
            data_collator = self.data_collator 
        )
        print("Trainer device:", trainer.args.device)

        # Finetune the model
        torch.cuda.empty_cache()
        print('\nModel training started ....')
        trainer.train()

        # Save best model
        trainer.save_model()
        return trainer

    def get_labels(self, tokenized_dataset, batch_size = 4, sample_set = 'train'):
        """
        Get the predictions from the trained model.
        """
        def collate_fn(batch):
            input_ids = [torch.tensor(example['input_ids']) for example in batch]
            input_ids = pad_sequence(input_ids, batch_first=True, padding_value=self.tokenizer.pad_token_id)
            return input_ids
        
        dataloader = DataLoader(tokenized_dataset[sample_set], batch_size=batch_size, collate_fn=collate_fn)
        predicted_output = []
        self.model.to(self.device)
        self.model.eval()
        print('Model loaded to: ', self.device)
        with torch.no_grad():
            for batch in tqdm(dataloader):
                batch = batch.to(self.device)
                output_ids = self.model.generate(batch)
                output_texts = self.tokenizer.batch_decode(output_ids, skip_special_tokens=True)
                for output_text in output_texts:
                    predicted_output.append(output_text)
        return predicted_output
    
    def get_metrics(self, y_true, y_pred):
        return precision_score(y_true, y_pred, average='macro'), recall_score(y_true, y_pred, average='macro'), \
            f1_score(y_true, y_pred, average='macro'), accuracy_score(y_true, y_pred)
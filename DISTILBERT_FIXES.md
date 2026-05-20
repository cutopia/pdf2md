# DistilBERT Issues and Fixes

## Issues Identified

### 1. Model Architecture Mismatch
**Error:**
```
Key                     | Status     | 
------------------------+------------+-
vocab_projector.bias    | UNEXPECTED | 
vocab_layer_norm.weight | UNEXPECTED | 
vocab_transform.bias    | UNEXPECTED | 
vocab_layer_norm.bias   | UNEXPECTED | 
vocab_transform.weight  | UNEXPECTED | 
classifier.weight       | MISSING    | 
pre_classifier.bias     | MISSING    | 
classifier.bias         | MISSING    | 
pre_classifier.weight   | MISSING    | 
```

**Cause:** The code was loading `distilbert-base-uncased` (a base model) and trying to use it for sequence classification without proper weights. The base DistilBERT model doesn't have classification head weights.

**Fix:** Changed the model name to `distilbert-base-uncased-finetated-sst-2-english`, which is a version of DistilBERT that has been pretrained for text classification on the SST-2 dataset.

### 2. Sequence Length Exceeded
**Error:**
```
Warning: Insufficient text from page 5
[transformers] Token indices sequence length is longer than the specified maximum sequence length for this model (579 > 512). Running this sequence through the model will result in indexing errors
Model inference error: The size of tensor a (579) must match the size of tensor b (512) at non-singleton dimension 1
```

**Cause:** The `_prepare_input_with_context` method concatenates multiple lines without truncation, resulting in text that exceeds DistilBERT's maximum sequence length of 512 tokens.

**Fixes Applied:**
1. Added truncation to the classifier pipeline initialization with `truncation=True` and `max_length=512`
2. Added explicit truncation in `_prepare_input_with_context()` method
3. Added truncation in `is_heading()` method before calling the classifier

## Changes Made

### File: `model_heading_detector.py`

#### Change 1: Updated model name (line ~48)
```python
# Before:
model_name = "distilbert-base-uncased"

# After:
model_name = "distilbert-base-uncased-finetated-sst-2-english"
```

#### Change 2: Added truncation to classifier pipeline (lines ~60-71)
```python
self.classifier = pipeline(
    "text-classification",
    model=self.model,
    tokenizer=self.tokenizer,
    device=-1,  # CPU only for compatibility
    truncation=True,
    max_length=512
)
```

#### Change 3: Added truncation in `is_heading()` method (lines ~100-116)
```python
try:
    # Truncate input to model's max sequence length
    max_length = self.tokenizer.model_max_length if hasattr(self.tokenizer, 'model_max_length') else 512
    truncated_text = full_text[:max_length * 4]  # Rough estimate: ~4 chars per token
    
    result = self.classifier(truncated_text, truncation=True, max_length=max_length)[0]
    
    # The model outputs 'LABEL_0' for non-heading and 'LABEL_1' for heading
    is_heading = result['label'] == 'LABEL_1'
    confidence = result['score']
    
    return (is_heading, confidence)
```

#### Change 4: Added truncation in `_prepare_input_with_context()` method (lines ~136-142)
```python
# Truncate to model's max sequence length (512 tokens for DistilBERT)
max_length = self.tokenizer.model_max_length if hasattr(self.tokenizer, 'model_max_length') else 512
if len(context_text) > max_length * 4:  # Rough estimate: ~4 chars per token
    context_text = context_text[:max_length * 4]
```

## Alternative Solutions

If you want to use a different model or train your own:

### Option A: Use a different pretrained classification model
```python
model_name = "textattack/distilbert-base-uncased-MRPC"  # Another classification model
```

### Option B: Train on your own heading data
1. Collect labeled examples of headings vs non-headings
2. Fine-tune DistilBERT on this dataset:
```python
from transformers import Trainer, TrainingArguments

training_args = TrainingArguments(
    output_dir="./heading_classifier",
    num_train_epochs=3,
    per_device_train_batch_size=16,
    per_device_eval_batch_size=64,
    warmup_steps=500,
    weight_decay=0.01,
    logging_dir='./logs',
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
)
trainer.train()
```

### Option C: Use a smaller, more efficient model
```python
model_name = "prajjwal1/bert-tiny"  # Smaller BERT variant
# or
model_name = "mrm8488/distilroberta-base-finetuned-sst-2-english"
```

## Testing

After applying these fixes, test with:
```bash
python -c "
from model_heading_detector import ModelHeadingDetector
detector = ModelHeadingDetector()
detector.initialize()
is_heading, confidence = detector.is_heading('Introduction to the Game')
print(f'Is heading: {is_heading}, Confidence: {confidence:.2f}')
"
```

## Notes

- The `UNEXPECTED` weights can be safely ignored when loading from a different task/architecture
- The `MISSING` weights are newly initialized and will need training on your downstream task for optimal performance
- For production use, consider using a model that's already fine-tuned for your specific domain

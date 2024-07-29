# train_sales_model.py
import os
import time
from transformers import AutoTokenizer, AutoModelForCausalLM, Trainer, TrainingArguments, DataCollatorForLanguageModeling
from datasets import Dataset
from dotenv import load_dotenv
from utils.database import fetch_sales_data
import logging

# Start timer
start_time = time.time()

# Initial print statement
print("Sales Model Training Script Initiated.")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
print("Loading environment variables...")
load_dotenv()

# Fetch sales data
print("Fetching sales data...")
sales_data = fetch_sales_data()
print(f"Fetched sales data: {len(sales_data)} records.")

# Ensure the sales_data DataFrame has a 'text' column for tokenization
if 'text' not in sales_data.columns:
    print("Creating text field...")
    sales_data['text'] = sales_data.apply(lambda row: ' '.join(row.values.astype(str)), axis=1)
    print("Text field created.")

# Tokenization
print("Initializing tokenizer...")
tokenizer = AutoTokenizer.from_pretrained('distilgpt2')
print("Tokenizer initialized.")

# Add padding token if not already present
if tokenizer.pad_token is None:
    print("Setting pad token...")
    tokenizer.pad_token = tokenizer.eos_token
    print("Pad token set.")

# Function for tokenization
def tokenize_function(examples):
    return tokenizer(examples['text'], padding="max_length", truncation=True)

# Convert DataFrame to Dataset
print("Converting DataFrame to Dataset...")
dataset = Dataset.from_pandas(sales_data[['text']])
print(f"Dataset created with {len(dataset)} examples.")

# Tokenize dataset
print("Tokenizing dataset...")
tokenized_dataset = dataset.map(tokenize_function, batched=True)
print("Dataset tokenized.")

# Split the data using Hugging Face's train_test_split method
print("Splitting dataset into training and evaluation sets...")
train_test_ratio = 0.2
train_test_split = tokenized_dataset.train_test_split(test_size=train_test_ratio)
train_dataset = train_test_split['train']
eval_dataset = train_test_split['test']
print(f"Training set: {len(train_dataset)}, Evaluation set: {len(eval_dataset)}")

# For testing purposes, reduce the dataset size
small_train_dataset = train_dataset.select(range(20))
small_eval_dataset = eval_dataset.select(range(4))
print(f"Reduced training set: {len(small_train_dataset)}, Reduced evaluation set: {len(small_eval_dataset)}")

# Define data collator
print("Defining data collator...")
data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)
print("Data collator defined.")

# Model initialization
print("Initializing model...")
model = AutoModelForCausalLM.from_pretrained('distilgpt2')
print("Model initialized.")

# Training arguments
print("Setting training arguments...")
training_args = TrainingArguments(
    output_dir='fine_tuned_sales_model',
    overwrite_output_dir=True,
    num_train_epochs=1,  # Reduce the number of epochs for testing
    per_device_train_batch_size=2,  # Reduce batch size
    save_steps=500,  # Adjust save steps
    save_total_limit=2,
    logging_dir='./logs',
    logging_steps=50,  # Adjust logging steps
)
print("Training arguments set.")

# Trainer initialization
print("Initializing trainer...")
trainer = Trainer(
    model=model,
    args=training_args,
    data_collator=data_collator,
    train_dataset=small_train_dataset,
    eval_dataset=small_eval_dataset,
)
print("Trainer initialized.")

# Train the model
logger.info("Starting training...")
print("Starting training...")
trainer.train()
print("Training completed.")

# Save the model and tokenizer
logger.info("Saving the model and tokenizer...")
print("Saving the model and tokenizer...")
trainer.save_model('fine_tuned_sales_model')
tokenizer.save_pretrained('fine_tuned_sales_model')
logger.info("Model and tokenizer saved successfully.")
print("Model and tokenizer saved successfully.")

# End timer and print duration
end_time = time.time()
print(f"Total execution time: {end_time - start_time:.2f} seconds.")

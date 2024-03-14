# import torch
# from transformers import GPT2Tokenizer, GPT2LMHeadModel
# from torch.utils.data import Dataset, DataLoader

# class CodeDataset(Dataset):
#     def __init__(self, data, tokenizer, max_length=128):
#         self.data = data
#         self.tokenizer = tokenizer
#         self.max_length = max_length

#     def __len__(self):
#         return len(self.data)

#     def __getitem__(self, idx):
#         prompt, code = self.data[idx]
#         inputs = self.tokenizer.encode(prompt, return_tensors="pt", max_length=self.max_length, truncation=True)
#         labels = self.tokenizer.encode(code, return_tensors="pt", max_length=self.max_length, truncation=True)
#         return inputs, labels

# # Pre-trained GPT-2 model and tokenizer
# tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
# model = GPT2LMHeadModel.from_pretrained("gpt2")

# # Original dataset (prompts and corresponding code snippets)
# dataset = [
#     ("add two numbers", "def add(a, b):\n    return a + b\n"),
#     ("subtract two numbers", "def subtract(a, b):\n    return a - b\n"),
#     ("multiply two numbers", "def multiply(a, b):\n    return a * b\n"),
#     ("divide two numbers", "def divide(a, b):\n    return a / b\n"),
# ]

# # Create dataset and dataloader
# code_dataset = CodeDataset(dataset, tokenizer)
# dataloader = DataLoader(code_dataset, batch_size=2, shuffle=True)

# # Fine-tune the model
# optimizer = torch.optim.AdamW(model.parameters(), lr=5e-5)
# for inputs, labels in dataloader:
#     inputs = inputs.to(model.device)
#     labels = labels.to(model.device)
#     outputs = model(inputs, labels=labels)
#     loss = outputs.loss
#     loss.backward()
#     optimizer.step()
#     optimizer.zero_grad()

# # Generate code snippets based on prompts
# prompt = input("Enter a prompt: ")
# prompt_inputs = tokenizer.encode(prompt, return_tensors="pt")
# outputs = model.generate(prompt_inputs, max_length=128, num_return_sequences=1)
# generated_code = tokenizer.decode(outputs[0], skip_special_tokens=True)

# print("Generated Code:")
# print(generated_code)

# from keras.models import load_model
# import cv2
# import numpy as np

# Load the saved model
# loaded_model = load_model("./trainedModels/cnn.h5")

# Load and preprocess the image
# img = cv2.imread('./dog.4001.jpg')
# img = cv2.resize(img, (64, 64))  # Replace with your input dimensions
# img = img.astype('float32') / 255  # Normalize pixel values
# img = np.expand_dims(img, axis=0)  # Add batch dimension

# Perform prediction
# predictions = loaded_model.predict(img)
# print(predictions)
# Interpret prediction (e.g., class labels)
# You need to define your classes to interpret the prediction output
# For example, if you have binary classification (cat or not cat), you might do:
# if predictions[0] > 0.5:
#     print("It's a cat!")
# else:
#     print("It's a dog!.")

import cv2

# Set the address of your DroidCam device
# This will typically be an IP address and port
# Example: 'http://192.168.0.100:4747/video'
droidcam_address = '192.168.1.103:4747'

# Create a VideoCapture object
cap = cv2.VideoCapture(droidcam_address)

# Check if the camera opened successfully
if not cap.isOpened():
    print("Error: Could not open DroidCam")
    exit()

# Read and display frames from the DroidCam
while True:
    ret, frame = cap.read()

    # Check if frame is None (i.e., end of video stream)
    if frame is None:
        print("Error: No frame received")
        break

    # Display the frame
    cv2.imshow('DroidCam', frame)

    # Exit if 'q' key is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the VideoCapture object and close all windows
cap.release()
cv2.destroyAllWindows()

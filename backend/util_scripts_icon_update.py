import os
import json
import re

# 1. Update Icons in Navbar and LandingPage
navbar_path = r'd:\practice\AIML-vlab\frontend\src\components\Navbar\Navbar.js'
with open(navbar_path, 'r', encoding='utf-8') as f:
    nav = f.read()

nav = re.sub(r'<span className="brand-icon">.*?</span>', '<span className="brand-icon">🧪</span>', nav, flags=re.DOTALL)

with open(navbar_path, 'w', encoding='utf-8') as f:
    f.write(nav)

landing_path = r'd:\practice\AIML-vlab\frontend\src\components\LandingPage\LandingPage.js'
with open(landing_path, 'r', encoding='utf-8') as f:
    land = f.read()

land = land.replace('🚀 AIML Lab', '🧪 AIML Lab')

with open(landing_path, 'w', encoding='utf-8') as f:
    f.write(land)

# 2. Update models.json with detailed descriptions for YOLO, ResNet, LSTM, StyleGAN
models_path = r'd:\practice\AIML-vlab\frontend\src\components\models.json'
with open(models_path, 'r', encoding='utf-8') as f:
    models = json.load(f)

detailed_updates = {
    'resnet': [
        {
            "parameter": "ResNet50 Backbone (Pre-trained on ImageNet)",
            "description": "A very deep foundational Convolutional Neural Network pretrained on millions of images. Think of it as an 'expert eye' that already knows how to detect edges, textures, and basic objects. Using skip-connections, it overcomes the vanishing gradient problem in deep networks."
        },
        {
            "parameter": "Freeze Base Model Weights",
            "description": "When checked, the pretrained 'expert eye' remains locked, and only your newly added Dense Classification Head learns from the custom dataset. This is much faster and requires less data. Unchecking means 'Fine-Tuning', where the entire network adjusts its core vision to your specific images (slower, but potentially more accurate)."
        },
        {
            "parameter": "Custom Classification Head",
            "description": "The custom decision-making layers attached to the end of the ResNet vision pipeline. This adapts the generic vision into your specific categories (e.g., Dog vs Cat, or X-Ray diagnosis)."
        },
        {
            "parameter": "Dense Layer Units",
            "description": "The number of neurons in a hidden layer. More units allow learning more complex logic combinations, but increase the risk of over-memorizing the training dataset (overfitting)."
        },
        {
            "parameter": "Activation (ReLU/Softmax/etc.)",
            "description": "The mathematical spark that allows the model to learn non-linear patterns. ReLU disables negative outputs, while Softmax converts final scores into percentages totaling 100%."
        },
        {
            "parameter": "Dropout",
            "description": "A regularization technique where random neurons are 'turned off' during training. This forces the network to learn robust, generalized patterns instead of relying heavily on a few specific neurons, drastically reducing overfitting."
        },
        {
            "parameter": "Evaluation Metrics",
            "description": "Accuracy (Percentage of correct predictions) and Categorical/Binary Crossentropy Loss (How confident the model was in its mistakes, lower is better)."
        }
    ],
    'lstm': [
        {
            "parameter": "LSTM (Long Short-Term Memory)",
            "description": "A specialized Neural Network architecture designed for sequential data (like time-series, text, or audio). Unlike standard networks, LSTMs have internal 'memory cells' with gates (forget, input, output) that decide exactly what information to keep over time and what noise to discard."
        },
        {
            "parameter": "LSTM Cell Units",
            "description": "The dimensional size of the internal memory state. A larger number of units means the LSTM can track more simultaneous patterns over time (like tracking temperature, humidity, and wind speed simultaneously)."
        },
        {
            "parameter": "Return Sequences",
            "description": "If TRUE, the LSTM outputs its memory state at every single time step in the sequence (required when stacking multiple LSTM layers). If FALSE, it only outputs the final summarized memory state after reading the entire sequence (usually set to FALSE for the very last LSTM layer before a Dense classification head)."
        },
        {
            "parameter": "Dense Head Activation",
            "description": "After the time sequences are analyzed, Dense layers interpret the final result. Activation functions (ReLU, Sigmoid) determine the output bounds of these interpretations."
        },
        {
            "parameter": "Dropout / Recurrent Dropout",
            "description": "Randomly drops connections between units to prevent the sequence memory from overly relying on highly specific chronological coincidences in the training data."
        },
        {
            "parameter": "Evaluation Metrics",
            "description": "Commonly measures Mean Squared Error (MSE) or Mean Absolute Error (MAE) for forecasting numerical sequences, or Accuracy for classifying a sequence category."
        }
    ],
    'yolo': [
        {
            "parameter": "YOLOv8 (You Only Look Once)",
            "description": "A state-of-the-art, single-shot real-time bounding box object detection model. It divides an image into a grid and simultaneously predicts the coordinates of boxes and the probability of classes inside those boxes in one swift pass."
        },
        {
            "parameter": "Epochs",
            "description": "The number of complete passes the YOLO network makes over the entire training dataset. YOLO often requires 50-100+ epochs to refine bounding box precision."
        },
        {
            "parameter": "Batch Size",
            "description": "How many images are passed through the network simultaneously before the weights are updated. Smaller batch sizes (8 or 16) are needed for high-resolution images to prevent Video RAM (VRAM) out-of-memory crashes."
        },
        {
            "parameter": "Image Resolution (imgsz)",
            "description": "The square pixel dimension that training images are resized to before processing (e.g., 640 for 640x640px). Higher resolutions allow detecting smaller objects but require exponentially more RAM and computing power."
        },
        {
            "parameter": "Initial Learning Rate (lr0)",
            "description": "The initial step size the optimizer takes when adjusting bounding box weights. If set too high, bounding boxes will wildly bounce around the target. If too low, it takes forever to converge on the correct box."
        },
        {
            "parameter": "Optimizer",
            "description": "The algorithm managing the weight updates. 'Adam' is usually safer for customized sets, while 'SGD' (Stochastic Gradient Descent) is standard for massive datasets."
        },
        {
            "parameter": "Evaluation Metrics (mAP50)",
            "description": "Mean Average Precision at 50% Intersection over Union. This measures what percentage of the predicted bounding boxes overlap with the real actual targets by at least 50%."
        }
    ],
    'stylegan': [
        {
            "parameter": "StyleGAN",
            "description": "An advanced Generative Adversarial Network that synthesizes hyper-realistic, high-resolution new images. It works by progressively generating imagery from low resolution up to high resolution, allowing unprecedented control over overarching layout ('coarse styles') down to fine textures ('fine styles')."
        },
        {
            "parameter": "Generative Adversarial Network Pipeline",
            "description": "Two neural networks fundamentally competing against one another: A Generator trying to forge fake images, and a Discriminator trying to act as an art-detective catching the fakes. Over time, the Generator becomes a master forger."
        },
        {
            "parameter": "Latent Dimension Z (z_dim)",
            "description": "The size of the initial random noise vector. Think of this as the size of the 'seed' of pure randomness that the network uses as a starting point to spark a specific generated image."
        },
        {
            "parameter": "Intermediate Latent Dimension W (w_dim)",
            "description": "StyleGAN's biggest innovation. It takes the random 'Z' vector and maps it onto an unentangled 'W' space. This allows you to specifically alter one visual feature (like hair color) without accidentally changing another feature (like face shape)."
        },
        {
            "parameter": "Log Resolution",
            "description": "The mathematical target scale of the final generated image. A Log2 value of 6 generates 64x64px images, 8 generates 256x256px, and 10 produces 1024x1024px images. Higher resolutions require massive VRAM and take exponentially longer to train."
        },
        {
            "parameter": "Batch Size / Epochs",
            "description": "Standard training loops parameters. For Generative modeling, you often deal with very small batch sizes (e.g., 4 or 8) due to high image VRAM footprints, compensated by very large epoch counts."
        }
    ]
}

for m in models:
    if m['code'] in detailed_updates:
        # We replace entirely to be deeply detailed
        m['description'] = detailed_updates[m['code']]

with open(models_path, 'w', encoding='utf-8') as f:
    json.dump(models, f, indent=4)

print('Update successful.')

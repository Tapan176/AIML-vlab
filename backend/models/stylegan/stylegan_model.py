import os
import torch
from torch import nn, optim
from torchvision import datasets, transforms
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset
from math import log2, sqrt
import numpy as np
from PIL import Image


# -----------------
# Flat Image Dataset (no class subfolders needed)
# -----------------
class _FlatImageDataset(Dataset):
    """Loads images from a flat directory without requiring class subfolders.
    Used for generative models like StyleGAN that don't need class labels."""
    IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp', '.tiff'}
    
    def __init__(self, root_dir, transform=None):
        self.root_dir = root_dir
        self.transform = transform
        self.image_paths = []
        
        # Walk all directories recursively to find images
        for dirpath, _, filenames in os.walk(root_dir):
            for fname in filenames:
                if os.path.splitext(fname)[1].lower() in self.IMAGE_EXTS and not fname.startswith('.'):
                    self.image_paths.append(os.path.join(dirpath, fname))
        
        self.image_paths.sort()
    
    def __len__(self):
        return len(self.image_paths)
    
    def __getitem__(self, idx):
        img = Image.open(self.image_paths[idx]).convert('RGB')
        if self.transform:
            img = self.transform(img)
        return img, 0  # Return 0 as dummy label


# -----------------
# Network Architectures
# -----------------
class EqualizedWeight(nn.Module):
    def __init__(self, shape):
        super().__init__()
        self.c = 1 / sqrt(np.prod(shape[1:]))
        self.weight = nn.Parameter(torch.randn(shape))
    def forward(self):
        return self.weight * self.c

class EqualizedLinear(nn.Module):
    def __init__(self, in_features, out_features, bias = 0.):
        super().__init__()
        self.weight = EqualizedWeight([out_features, in_features])
        self.bias = nn.Parameter(torch.ones(out_features) * bias)
    def forward(self, x: torch.Tensor):
        return F.linear(x, self.weight(), bias=self.bias)

class EqualizedConv2d(nn.Module):
    def __init__(self, in_features, out_features, kernel_size, padding = 0):
        super().__init__()
        self.padding = padding
        self.weight = EqualizedWeight([out_features, in_features, kernel_size, kernel_size])
        self.bias = nn.Parameter(torch.ones(out_features))
    def forward(self, x: torch.Tensor):
        return F.conv2d(x, self.weight(), bias=self.bias, padding=self.padding)

class Conv2dWeightModulate(nn.Module):
    def __init__(self, in_features, out_features, kernel_size, demodulate = True, eps = 1e-8):
        super().__init__()
        self.out_features = out_features
        self.demodulate = demodulate
        self.padding = (kernel_size - 1) // 2
        self.weight = EqualizedWeight([out_features, in_features, kernel_size, kernel_size])
        self.eps = eps
    def forward(self, x, s):
        b, _, h, w = x.shape
        s = s[:, None, :, None, None]
        weights = self.weight()[None, :, :, :, :]
        weights = weights * s
        if self.demodulate:
            sigma_inv = torch.rsqrt((weights ** 2).sum(dim=(2, 3, 4), keepdim=True) + self.eps)
            weights = weights * sigma_inv
        x = x.reshape(1, -1, h, w)
        _, _, *ws = weights.shape
        weights = weights.reshape(b * self.out_features, *ws)
        x = F.conv2d(x, weights, padding=self.padding, groups=b)
        return x.reshape(-1, self.out_features, h, w)

class ToRGB(nn.Module):
    def __init__(self, W_DIM, features):
        super().__init__()
        self.to_style = EqualizedLinear(W_DIM, features, bias=1.0)
        self.conv = Conv2dWeightModulate(features, 3, kernel_size=1, demodulate=False)
        self.bias = nn.Parameter(torch.zeros(3))
        self.activation = nn.LeakyReLU(0.2, True)
    def forward(self, x, w):
        style = self.to_style(w)
        x = self.conv(x, style)
        return self.activation(x + self.bias[None, :, None, None])

class MappingNetwork(nn.Module):
    def __init__(self, z_dim, w_dim):
        super().__init__()
        self.mapping = nn.Sequential(
            EqualizedLinear(z_dim, w_dim), nn.ReLU(),
            EqualizedLinear(z_dim, w_dim), nn.ReLU(),
            EqualizedLinear(z_dim, w_dim), nn.ReLU(),
            EqualizedLinear(z_dim, w_dim), nn.ReLU(),
            EqualizedLinear(z_dim, w_dim), nn.ReLU(),
            EqualizedLinear(z_dim, w_dim), nn.ReLU(),
            EqualizedLinear(z_dim, w_dim), nn.ReLU(),
            EqualizedLinear(z_dim, w_dim)
        )
    def forward(self, x):
        x = x / torch.sqrt(torch.mean(x ** 2, dim=1, keepdim=True) + 1e-8)
        return self.mapping(x)

class StyleBlock(nn.Module):
    def __init__(self, W_DIM, in_features, out_features):
        super().__init__()
        self.to_style = EqualizedLinear(W_DIM, in_features, bias=1.0)
        self.conv = Conv2dWeightModulate(in_features, out_features, kernel_size=3)
        self.scale_noise = nn.Parameter(torch.zeros(1))
        self.bias = nn.Parameter(torch.zeros(out_features))
        self.activation = nn.LeakyReLU(0.2, True)
    def forward(self, x, w, noise):
        s = self.to_style(w)
        x = self.conv(x, s)
        if noise is not None:
            x = x + self.scale_noise[None, :, None, None] * noise
        return self.activation(x + self.bias[None, :, None, None])

class GeneratorBlock(nn.Module):
    def __init__(self, W_DIM, in_features, out_features):
        super().__init__()
        self.style_block1 = StyleBlock(W_DIM, in_features, out_features)
        self.style_block2 = StyleBlock(W_DIM, out_features, out_features)
        self.to_rgb = ToRGB(W_DIM, out_features)
    def forward(self, x, w, noise):
        x = self.style_block1(x, w, noise[0])
        x = self.style_block2(x, w, noise[1])
        rgb = self.to_rgb(x, w)
        return x, rgb

class Generator(nn.Module):
    def __init__(self, log_resolution, W_DIM, n_features = 32, max_features = 256):
        super().__init__()
        features = [min(max_features, n_features * (2 ** i)) for i in range(log_resolution - 2, -1, -1)]
        self.n_blocks = len(features)
        self.initial_constant = nn.Parameter(torch.randn((1, features[0], 4, 4)))
        self.style_block = StyleBlock(W_DIM, features[0], features[0])
        self.to_rgb = ToRGB(W_DIM, features[0])
        blocks = [GeneratorBlock(W_DIM, features[i - 1], features[i]) for i in range(1, self.n_blocks)]
        self.blocks = nn.ModuleList(blocks)
    def forward(self, w, input_noise):
        batch_size = w.shape[1]
        x = self.initial_constant.expand(batch_size, -1, -1, -1)
        x = self.style_block(x, w[0], input_noise[0][1])
        rgb = self.to_rgb(x, w[0])
        for i in range(1, self.n_blocks):
            x = F.interpolate(x, scale_factor=2, mode="bilinear")
            x, rgb_new = self.blocks[i - 1](x, w[i], input_noise[i])
            rgb = F.interpolate(rgb, scale_factor=2, mode="bilinear") + rgb_new
        return torch.tanh(rgb)

class DiscriminatorBlock(nn.Module):
    def __init__(self, in_features, out_features):
        super().__init__()
        self.residual = nn.Sequential(nn.AvgPool2d(kernel_size=2, stride=2), EqualizedConv2d(in_features, out_features, kernel_size=1))
        self.block = nn.Sequential(
            EqualizedConv2d(in_features, in_features, kernel_size=3, padding=1),
            nn.LeakyReLU(0.2, True),
            EqualizedConv2d(in_features, out_features, kernel_size=3, padding=1),
            nn.LeakyReLU(0.2, True),
        )
        self.down_sample = nn.AvgPool2d(kernel_size=2, stride=2)
        self.scale = 1 / sqrt(2)
    def forward(self, x):
        residual = self.residual(x)
        x = self.block(x)
        x = self.down_sample(x)
        return (x + residual) * self.scale

class Discriminator(nn.Module):
    def __init__(self, log_resolution, n_features = 64, max_features = 256):
        super().__init__()
        features = [min(max_features, n_features * (2 ** i)) for i in range(log_resolution - 1)]
        self.from_rgb = nn.Sequential(EqualizedConv2d(3, n_features, 1), nn.LeakyReLU(0.2, True))
        n_blocks = len(features) - 1
        blocks = [DiscriminatorBlock(features[i], features[i + 1]) for i in range(n_blocks)]
        self.blocks = nn.Sequential(*blocks)
        final_features = features[-1] + 1
        self.conv = EqualizedConv2d(final_features, final_features, 3)
        self.final = EqualizedLinear(2 * 2 * final_features, 1)
    def minibatch_std(self, x):
        batch_statistics = torch.std(x, dim=0).mean().repeat(x.shape[0], 1, x.shape[2], x.shape[3])
        return torch.cat([x, batch_statistics], dim=1)
    def forward(self, x):
        x = self.from_rgb(x)
        x = self.blocks(x)
        x = self.minibatch_std(x)
        x = self.conv(x)
        x = x.reshape(x.shape[0], -1)
        return self.final(x)

# -----------------
# API Handler
# -----------------
def get_noise(batch_size, log_resolution, device):
    noise = []
    resolution = 4
    for i in range(log_resolution):
        if i == 0:
            n1 = None
        else:
            n1 = torch.randn(batch_size, 1, resolution, resolution, device=device)
        n2 = torch.randn(batch_size, 1, resolution, resolution, device=device)
        noise.append((n1, n2))
        resolution *= 2
    return noise

def train_stylegan(body, validated_params, user_id=None, session_version=None):
    """
    Performs real StyleGAN training on the user's image dataset.
    All hyperparameters are sourced from validated_params.
    """
    import time
    import json
    from torch.utils.data import DataLoader
    from torchvision import datasets, transforms
    from services.dataset_resolver import resolve_image_dataset_path

    file_path = body.get('filePath')
    filename = body.get('filename')
    
    # All hyperparams from validated_params (set by user via HyperparamPanel)
    epochs = int(validated_params.get('epochs', 300))
    batch_size = int(validated_params.get('batch_size', 8))
    z_dim = int(validated_params.get('z_dim', 256))
    w_dim = int(validated_params.get('w_dim', 256))
    log_resolution = int(validated_params.get('log_resolution', 7))
    lr = float(validated_params.get('learning_rate', 0.0001))
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    resolution = 2 ** log_resolution
    
    yield f"data: {json.dumps({'log': f'StyleGAN Process initialized on {device}. Resolution: {resolution}x{resolution}'})}\n\n"
    yield f"data: {json.dumps({'log': f'Config: epochs={epochs}, batch={batch_size}, z_dim={z_dim}, w_dim={w_dim}, lr={lr}'})}\n\n"
    
    # --- Resolve dataset path ---
    try:
        dataset_path = resolve_image_dataset_path(user_id, filename=filename, file_path=file_path)
    except FileNotFoundError as e:
        yield f"data: {json.dumps({'error': str(e)})}\n\n"
        return

    yield f"data: {json.dumps({'log': f'Dataset path resolved: {dataset_path}'})}\n\n"

    try:
        # Data preparation
        transform = transforms.Compose([
            transforms.Resize((resolution, resolution)),
            transforms.ToTensor(),
            transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),
        ])
        
        # For StyleGAN, always use flat image loader since we don't need class labels
        # This handles both flat directories and directories with subfolders
        dataset = _FlatImageDataset(dataset_path, transform)
        
        # If no images found with flat loader, try ImageFolder as fallback
        if len(dataset) == 0:
            # Check if directory has class subfolders
            has_subdirs = any(
                os.path.isdir(os.path.join(dataset_path, d))
                for d in os.listdir(dataset_path)
                if not d.startswith('.') and d != '__MACOSX'
            )
            
            if has_subdirs:
                try:
                    dataset = datasets.ImageFolder(root=dataset_path, transform=transform)
                except Exception as e:
                    yield f"data: {json.dumps({'error': f'Failed to load dataset: {str(e)}'})}\n\n"
                    return
        
        if len(dataset) == 0:
            yield f"data: {json.dumps({'error': f'No images found in {dataset_path}. Check dataset structure.'})}\n\n"
            return
        
        loader = DataLoader(dataset, batch_size=batch_size, shuffle=True, num_workers=0)

        
        yield f"data: {json.dumps({'log': f'Loaded {len(dataset)} images from dataset.'})}\n\n"
        
        # Initialize Models
        gen = Generator(log_resolution, w_dim).to(device)
        disc = Discriminator(log_resolution).to(device)
        map_net = MappingNetwork(z_dim, w_dim).to(device)
        
        opt_gen = optim.Adam(list(gen.parameters()) + list(map_net.parameters()), lr=lr, betas=(0.0, 0.99))
        opt_disc = optim.Adam(disc.parameters(), lr=lr, betas=(0.0, 0.99))
        
        yield f"data: {json.dumps({'log': f'Starting Real Training for {epochs} epochs...'})}\n\n"
        
        final_loss_g = 0
        final_loss_d = 0
        
        for epoch in range(1, epochs + 1):
            total_loss_g = 0
            total_loss_d = 0
            num_batches = 0
            
            for i, (real, _) in enumerate(loader):
                real = real.to(device)
                cur_batch_size = real.shape[0]
                
                # Train Discriminator
                noise = torch.randn(cur_batch_size, z_dim).to(device)
                w = map_net(noise).unsqueeze(0).repeat(log_resolution - 1, 1, 1)
                
                input_noise = get_noise(cur_batch_size, log_resolution, device)
                fake = gen(w, input_noise)
                
                disc_real = disc(real)
                disc_fake = disc(fake.detach())
                
                loss_d = -(torch.mean(disc_real) - torch.mean(disc_fake))
                
                opt_disc.zero_grad()
                loss_d.backward()
                opt_disc.step()
                
                # Train Generator
                gen_fake = disc(fake)
                loss_g = -torch.mean(gen_fake)
                
                opt_gen.zero_grad()
                loss_g.backward()
                opt_gen.step()
                
                total_loss_g += loss_g.item()
                total_loss_d += loss_d.item()
                num_batches += 1

            if num_batches > 0:
                avg_loss_g = total_loss_g / num_batches
                avg_loss_d = total_loss_d / num_batches
            else:
                avg_loss_g = 0
                avg_loss_d = 0
            
            final_loss_g = avg_loss_g
            final_loss_d = avg_loss_d
            
            yield f"data: {json.dumps({'log': f'Epoch [{epoch}/{epochs}] Loss D: {avg_loss_d:.4f}, Loss G: {avg_loss_g:.4f}'})}\n\n"
            
            time.sleep(0.05)

        # Save model
        from utils.saveTrainedModel import saveTrainedModel
        save_path = saveTrainedModel(gen, "stylegan", "PyTorch", user_id=user_id, version=session_version)
        
        yield f"data: {json.dumps({'log': f'Training Complete! Model saved.'})}\n\n"
        yield f"data: {json.dumps({'status': 'training_complete', 'trained_model_path': save_path, 'epochs_trained': epochs, 'loss_d': float(final_loss_d), 'loss_g': float(final_loss_g)})}\n\n"

    except Exception as e:
        yield f"data: {json.dumps({'error': f'Training failed: {str(e)}'})}\n\n"

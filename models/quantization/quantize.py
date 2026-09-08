import os
import torch
import torch.nn as nn

# Define the same CNN architecture to load the saved state dictionary
class PotatoBinaryCNN(nn.Module):
    def __init__(self):
        super(PotatoBinaryCNN, self).__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 16, kernel_size=3, stride=1, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),
            
            nn.Conv2d(16, 32, kernel_size=3, stride=1, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2, 2)
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(32 * 32 * 32, 64),
            nn.ReLU(),
            nn.Linear(64, 1)
        )

    def forward(self, x):
        x = self.features(x)
        x = self.classifier(x)
        return x

def quantize_weights():
    # 1. Load the trained float32 weights from the training stage
    model_path = "../weights/potato_model.pth"
    if not os.path.exists(model_path):
        print(f"Error: Could not find weights at {model_path}")
        return

    model = PotatoBinaryCNN()
    model.load_state_dict(torch.load(model_path, map_location="cpu"))
    model.eval()
    print("Successfully loaded trained float32 model weights.")

    # 2. Perform Post-Training Quantization (INT8 mapping)
    print("Quantizing weights to INT8 range [-128, 127]...")
    quantized_state_dict = {}
    
    for name, param in model.state_dict().items():
        if "weight" in name or "bias" in name:
            # Find scaling factor for symmetric INT8 quantization
            max_val = torch.max(torch.abs(param))
            scale = max_val / 127.0 if max_val > 0 else 1.0
            
            # Quantize and clamp to 8-bit signed integer boundaries
            quantized_param = torch.clamp(torch.round(param / scale), -128, 127).to(torch.int8)
            quantized_state_dict[name] = {
                "values": quantized_param,
                "scale": scale
            }

    # 3. Save quantized representation for MIF export
    os.makedirs("../export", exist_ok=True)
    torch.save(quantized_state_dict, "../export/quantized_weights.pth")
    print("INT8 quantization complete! Saved to ../export/quantized_weights.pth")

if __name__ == "__main__":
    quantize_weights()

import os
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, random_split
from torchvision import datasets, transforms

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
        return self.classifier(self.features(x))

def evaluate_model():
    # Automatically locate the datasets folder relative to this script's path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.abspath(os.path.join(script_dir, "datasets/Potato"))
    model_path = os.path.abspath(os.path.join(script_dir, "../weights/potato_model.pth"))

    print(f"Looking for dataset at: {data_dir}")
    print(f"Looking for weights at: {model_path}")

    transform = transforms.Compose([
        transforms.Resize((128, 128)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    if not os.path.exists(data_dir):
        print(f"Error: Dataset folder not found at {data_dir}")
        return

    dataset = datasets.ImageFolder(root=data_dir, transform=transform)
    dataset.target_transform = lambda idx: 0 if "healthy" in dataset.classes[idx].lower() else 1

    # Replicate the exact 80/20 train/test split deterministically
    torch.manual_seed(42)
    train_size = int(0.8 * len(dataset))
    test_size = len(dataset) - train_size
    _, test_dataset = random_split(dataset, [train_size, test_size])
    
    test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)

    model = PotatoBinaryCNN()
    if not os.path.exists(model_path):
        print(f"Error: Model weights not found at {model_path}")
        return
        
    model.load_state_dict(torch.load(model_path, map_location="cpu"))
    model.eval()

    correct = 0
    total = 0

    print("Evaluating model on test dataset...")
    with torch.no_grad():
        for images, labels in test_loader:
            outputs = model(images)
            preds = (torch.sigmoid(outputs) > 0.5).long().squeeze(1)
            correct += (preds == labels).sum().item()
            total += labels.size(0)

    accuracy = 100.0 * correct / total
    print(f"Evaluation Complete! Test Accuracy: {accuracy:.2f}%")

if __name__ == "__main__":
    evaluate_model()
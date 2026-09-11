import os
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, random_split
from torchvision import datasets, transforms
from torchvision import models
from sklearn.metrics import classification_report, confusion_matrix
import numpy as np

def evaluate_model():
    # Exact absolute paths
    data_dir = r"C:\Users\User\OneDrive\Desktop\edge-ai-coprocessor\models\training\datasets\Potato"
    model_path = r"C:\Users\User\OneDrive\Desktop\edge-ai-coprocessor\models\weights\potato_model_3class.pth"

    if not os.path.exists(data_dir):
        print(f"Error: Dataset path not found at: {data_dir}")
        return
    if not os.path.exists(model_path):
        print(f"Error: Weights file not found at: {model_path}")
        return

    # 1. Standard validation transforms
    transform = transforms.Compose([
        transforms.Resize((128, 128)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    # 2. Load dataset (automatically detects 3 classes: diseased_potato, healthy_potato, non_potato)
    dataset = datasets.ImageFolder(root=data_dir, transform=transform)
    class_names = dataset.classes
    print(f"Detected Classes: {class_names}")

    # 3. Same train/test split seed used during training
    torch.manual_seed(42)
    train_size = int(0.8 * len(dataset))
    test_size = len(dataset) - train_size
    _, test_dataset = random_split(dataset, [train_size, test_size])
    test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)

    # 4. Re-initialize MobileNetV2 3-class architecture
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = models.mobilenet_v2(weights=None)
    model.classifier[1] = nn.Sequential(
        nn.Dropout(p=0.3, inplace=True),
        nn.Linear(model.last_channel, len(class_names))
    )

    # 5. Load the trained weights
    model.load_state_dict(torch.load(model_path, map_location=device))
    model = model.to(device)
    model.eval()

    # 6. Run Evaluation
    all_preds = []
    all_labels = []

    print("Running evaluation on test/validation split...")
    with torch.no_grad():
        for inputs, labels in test_loader:
            inputs, labels = inputs.to(device), labels.to(device)
            outputs = model(inputs)
            _, predicted = torch.max(outputs, 1)

            all_preds.extend(predicted.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())

    # 7. Print Metrics
    print("\n--- Classification Report ---")
    print(classification_report(all_labels, all_preds, target_names=class_names))

    print("\n--- Confusion Matrix ---")
    print(confusion_matrix(all_labels, all_preds))

if __name__ == "__main__":
    evaluate_model()
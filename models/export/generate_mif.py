import os
import torch

def generate_mobilenet_conv1_mif():
    # Path to your saved 3-class MobileNetV2 model weights
    model_path = r"C:\Users\User\OneDrive\Desktop\edge-ai-coprocessor\models\weights\potato_model_3class.pth"
    
    if not os.path.exists(model_path):
        print(f"Error: Model weights not found at {model_path}")
        return

    # Load model state dict
    state_dict = torch.load(model_path, map_location="cpu")
    
    # MobileNetV2 first convolutional layer key in torchvision
    target_key = "features.0.0.weight"
    if target_key in state_dict:
        weights = state_dict[target_key]
    else:
        # Fallback search if key name varies slightly
        print(f"Warning: '{target_key}' not found. Searching state dict keys...")
        matching_keys = [k for k in state_dict.keys() if "features.0" in k and "weight" in k]
        if matching_keys:
            weights = state_dict[matching_keys[0]]
            print(f"Using fallback key: {matching_keys[0]}")
        else:
            weights = list(state_dict.values())[0]

    # Flatten the tensor into a 1D list
    flat_weights = weights.detach().numpy().flatten()
    
    # Quantize to INT8 for MIF format (-128 to 127)
    max_val = max(abs(flat_weights.min()), abs(flat_weights.max()))
    scale = 127.0 / max_val if max_val != 0 else 1.0
    quantized_weights = [int(round(w * scale)) for w in flat_weights]

    depth = len(quantized_weights)
    width = 8 # 8-bit width for INT8

    output_filename = "conv1_weights.mif"
    print(f"Generating {output_filename} | Depth: {depth} | Width: {width}")

    # Write out the standard Quartus MIF format
    with open(output_filename, "w") as f:
        f.write(f"WIDTH={width};\n")
        f.write(f"DEPTH={depth};\n\n")
        f.write("ADDRESS_RADIX=DEC;\n")
        f.write("DATA_RADIX=BIN;\n\n")
        f.write("CONTENT BEGIN\n")
        
        for i, val in enumerate(quantized_weights):
            # Convert signed int8 to 8-bit binary string
            bin_val = format(val & 0xFF, '08b')
            f.write(f"  {i} : {bin_val};\n")
            
        f.write("END;\n")

    print(f"Successfully generated {output_filename} for MobileNetV2!")

if __name__ == "__main__":
    generate_mobilenet_conv1_mif()
import torch
import os

def generate_conv1_mif():
    # Path to your saved PyTorch model weights
    model_path = "../weights/potato_model.pth"
    
    if not os.path.exists(model_path):
        print(f"Error: Model weights not found at {model_path}")
        return

    # Load model state dict
    state_dict = torch.load(model_path, map_location="cpu")
    
    # Extract Conv1 weights (features.0.weight)
    if "features.0.weight" in state_dict:
        weights = state_dict["features.0.weight"]
    else:
        # Fallback if keys differ
        weights = list(state_dict.values())[0]

    # Flatten the tensor into 1D list
    flat_weights = weights.detach().numpy().flatten()
    
    # Simple quantization to INT8 for MIF format (-128 to 127)
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

    print(f"Successfully generated {output_filename}!")

if __name__ == "__main__":
    generate_conv1_mif()
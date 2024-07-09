import torch
import torchvision.transforms as transforms
import torchvision.models as models
from PIL import Image
import os
import argparse

def load_model():
    model = models.mobilenet_v2(pretrained=True)
    model.classifier[1] = torch.nn.Linear(model.last_channel, 2)  # 2 classes: SFW and NSFW
    model.eval()
    return model

def preprocess_image(image_path):
    transform = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    image = Image.open(image_path).convert('RGB')
    return transform(image).unsqueeze(0)

def classify_image(model, image_tensor):
    with torch.no_grad():
        outputs = model(image_tensor)
        probabilities = torch.nn.functional.softmax(outputs, dim=1)
    return probabilities[0].tolist()

def main(image_path):
    model = load_model()
    image_tensor = preprocess_image(image_path)
    probabilities = classify_image(model, image_tensor)
    print(probabilities)
    is_nsfw = probabilities[1] > 0.6  # Assuming index 1 is NSFW
    nsfw_score = probabilities[1]

    return {
        'is_nsfw': is_nsfw,
        'nsfw_score': nsfw_score,
        'sfw_probability': probabilities[0],
        'nsfw_probability': probabilities[1]
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Classify an image using NSFW detection.")
    parser.add_argument("image_path", help="Path to the image file to classify")
    args = parser.parse_args()

    if not os.path.exists(args.image_path):
        print(f"Error: The file '{args.image_path}' does not exist.")
    else:
        try:
            result = main(args.image_path)
            print(f"Image: {args.image_path}")
            print(f"Is NSFW: {result['is_nsfw']}")
            print(f"NSFW Score: {result['nsfw_score']:.4f}")
            print(f"SFW Probability: {result['sfw_probability']:.4f}")
            print(f"NSFW Probability: {result['nsfw_probability']:.4f}")
        except Exception as e:
            print(f"An error occurred while processing the image: {str(e)}")

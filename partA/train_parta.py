# -*- coding: utf-8 -*-
"""train_parta.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1qlQHJMOP788ElwgfPDjmYd6_YnbTb1s6

# ****Question-1****
"""

import torch
import torch.nn as nn
import torch.nn.functional as F

class CNN(nn.Module):
    def __init__(self, input_shape, num_classes, num_filters, filter_size, activation_conv, activation_dense, num_neurons_dense):
        super(CNN, self).__init__()
        # Create convolutional layers
        self.conv_layers = self._create_conv_layers(input_shape[0], num_filters, filter_size, activation_conv)
        # Create fully connected layers
        self.fc_layers = nn.Sequential(
            nn.Linear(256 * 7 * 7, num_neurons_dense),  # Input size depends on the input_shape and max-pooling layers
            activation_dense,  # Activation function for the dense layer
            nn.Linear(num_neurons_dense, num_classes)  # Output layer
        )

    def _create_conv_layers(self, input_channels, num_filters, filter_size, activation_conv):
        layers = []
        in_channels = input_channels
        for _ in range(5):  # Reduced to 5 convolutional layers
            # Add convolutional layer
            layers += [
                nn.Conv2d(in_channels, num_filters, filter_size, padding=1),  # Convolutional layer
                activation_conv,  # Activation function
                nn.MaxPool2d(kernel_size=2, stride=2)  # Max-pooling layer
            ]
            in_channels = num_filters
        return nn.Sequential(*layers)

    def forward(self, x):
        # Forward pass through convolutional layers
        x = self.conv_layers(x)
        # Reshape tensor for fully connected layers
        x = x.view(x.size(0), -1)
        # Forward pass through fully connected layers
        x = self.fc_layers(x)
        return x

# Example parameters
input_shape = (3, 224, 224)  # Example shape compatible with iNaturalist dataset
num_classes = 10  # Number of classes in iNaturalist dataset
num_filters = 32  # Number of filters in convolutional layers
filter_size = 3  # Size of filters

# Define activation functions for convolutional and dense layers
activation_conv = nn.ReLU(inplace=True)  # Activation function for convolutional layers
activation_dense = nn.ReLU(inplace=True)  # Activation function for dense layer

num_neurons_dense = 1024  # Number of neurons in dense layer

# Create the model
model = CNN(input_shape, num_classes, num_filters, filter_size, activation_conv, activation_dense, num_neurons_dense)

print("Sample Model as asked in Question 1")
# Display model summary
print(model)

"""# **Question-2**"""

import torch
import torch.nn as nn
import torch.optim as optim
import torchvision
from torchvision import datasets, transforms
from torch.utils.data import DataLoader
from torch.utils.data import ConcatDataset
import torch.nn.functional as F
import torchvision.models as models
from PIL import Image
import os
import random
from collections import defaultdict  # Import defaultdict
import numpy as np
from torch.utils.data import random_split
from torch.utils.data import Subset
import matplotlib.pyplot as plt
import wandb
from tqdm import tqdm

# Set device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Define CNN architecture
class CNN(nn.Module):
    def __init__(self, input_channels, num_classes, num_filters, filter_organization, filter_size, activation, batch_normalization, dropout_value, num_nuerons):
        super(CNN, self).__init__()

        self.conv_layers = nn.ModuleList()  # ModuleList to store the convolutional layers

        # Define the convolutional layers dynamically using a loop
        padding = 1  # Padding size for convolutional layers

        # Determine activation function based on the provided activation argument
        if activation == 'relu':
            act = nn.ReLU()
        elif activation == 'gelu':
            act = nn.GELU()
        elif activation == 'silu':
            act = nn.SiLU()
        elif activation == 'mish':
            act = Mish()  # Custom activation function

        in_channels = input_channels  # Number of input channels

        out_size = 224  # Initial output size after convolutional layers

        # Loop to create convolutional layers
        for i in range(5):  # Create 5 convolutional layers
            self.conv_layers.append(nn.Conv2d(in_channels, num_filters, kernel_size=filter_size, padding=padding))

            # Add batch normalization layer if specified
            if batch_normalization:
                self.conv_layers.append(nn.BatchNorm2d(num_filters))

            self.conv_layers.append(act)  # Add activation function

            self.conv_layers.append(nn.MaxPool2d(kernel_size=2, stride=2))  # Max pooling layer

            # Add dropout layer if dropout value is specified
            if dropout_value > 0:
                self.conv_layers.append(nn.Dropout(dropout_value))

            in_channels = num_filters  # Update input channels for next layer

            # Update num_filters based on filter_organization
            if filter_organization == 'double':
                num_filters = int(num_filters * 2)
            elif filter_organization == 'halve':
                num_filters = int(num_filters / 2)
            elif filter_organization == 'same':
                num_filters = num_filters

            # Update out_size based on pooling parameters
            out_size = ((out_size + 2 * padding - 2) // 2) + 1

        # Define fully connected layers
        self.fc1 = nn.Linear(in_channels * (out_size - 1) * (out_size - 1), num_nuerons)
        self.fc2 = nn.Linear(num_nuerons, num_classes)

    def forward(self, x):
        # Forward pass through convolutional layers
        for layer in self.conv_layers:
            x = layer(x)

        # Flatten the output tensor
        x = x.view(-1, self.num_flat_features(x))

        # Forward pass through first fully connected layer with ReLU activation
        x = F.relu(self.fc1(x))

        # Forward pass through second fully connected layer
        x = self.fc2(x)
        return x

    # Function to calculate the number of features in the output tensor
    def num_flat_features(self, x):
        size = x.size()[1:]  # Exclude batch dimension
        num_features = 1
        for s in size:
            num_features *= s
        return num_features


# Custom activation function
class Mish(nn.Module):
    def forward(self, x):
        return x * torch.tanh(F.softplus(x))

def data_loader(train_data_folder, batch_size, data_augmentation):
    # Define the transformation for images without augmentation
    without_augmentation_transform = transforms.Compose([
        transforms.Resize((224, 224)),  # Resize images to 224x224
        transforms.ToTensor(),  # Convert images to PyTorch tensors
        transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))  # Normalize images
    ])

    # Load the original training dataset with the specified transformations
    train_dataset = datasets.ImageFolder(root=train_data_folder, transform=without_augmentation_transform)

    # Shuffle the dataset
    indices = list(range(len(train_dataset)))
    np.random.shuffle(indices)

    # Calculate the size of the validation set (20% of the training data)
    val_size = int(0.2 * len(train_dataset))

    # Calculate the number of samples per class for validation
    num_classes = len(train_dataset.classes)
    val_size_per_class = val_size // num_classes

    # Initialize lists to store indices for training and validation
    train_indices = []
    val_indices = []

    # Iterate through each class to select validation samples
    for class_idx in range(num_classes):
        class_indices = [i for i in indices if train_dataset.targets[i] == class_idx]
        val_indices.extend(class_indices[:val_size_per_class])
        train_indices.extend(class_indices[val_size_per_class:])

    # Apply data augmentation if specified
    if data_augmentation:
        # Define data augmentation transforms for training data
        train_transform = transforms.Compose([
            transforms.RandomHorizontalFlip(),  # Randomly flip images horizontally
            transforms.Resize((224, 224)),  # Resize images to 224x224
            transforms.RandomRotation(10),  # Randomly rotate images by up to 10 degrees
            transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),  # Adjust color brightness, contrast, and saturation
            transforms.ToTensor(),  # Convert images to PyTorch tensors
            transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))  # Normalize images
        ])

        # Create PyTorch data loaders for the original dataset and transformed dataset
        train_loader = DataLoader(Subset(train_dataset, train_indices), batch_size=batch_size, shuffle=True)
        val_loader = DataLoader(Subset(train_dataset, val_indices), batch_size=batch_size, shuffle=True)

        # Create transformed dataset and data loader
        transformed_dataset = datasets.ImageFolder(root=train_data_folder, transform=train_transform)
        transformed_loader = DataLoader(Subset(transformed_dataset, train_indices), batch_size=batch_size, shuffle=True)

        # Concatenate transformed datasets
        combined_train_dataset = ConcatDataset([train_loader.dataset, transformed_loader.dataset])

        # Define data loader for combined datasets
        train_loader = DataLoader(dataset=combined_train_dataset, batch_size=batch_size, shuffle=True)
    else:
        # If no data augmentation, create PyTorch data loaders for the original dataset only
        train_loader = DataLoader(Subset(train_dataset, train_indices), batch_size=batch_size, shuffle=True)
        val_loader = DataLoader(Subset(train_dataset, val_indices), batch_size=batch_size, shuffle=True)

    return train_loader, val_loader

# Define training function
def train(model, train_loader, optimizer, criterion, device):
    """
    Function to train the model using the training data.

    Args:
        model: The neural network model to be trained.
        train_loader: DataLoader for the training dataset.
        optimizer: Optimizer to update the model parameters.
        criterion: Loss function to compute the training loss.
        device: Device (CPU or GPU) where the data will be loaded.

    Returns:
        train_loss: Average training loss for the epoch.
        train_accuracy: Accuracy of the model on the training dataset.
    """
    model.train()  # Set the model to train mode
    running_loss = 0.0
    correct = 0
    total = 0

    # Iterate over the batches in the training DataLoader
    for inputs, labels in train_loader:
        inputs, labels = inputs.to(device), labels.to(device)
        optimizer.zero_grad()  # Zero the parameter gradients
        outputs = model(inputs)  # Forward pass
        loss = criterion(outputs, labels)  # Compute the loss
        loss.backward()  # Backward pass
        optimizer.step()  # Update weights
        running_loss += loss.item()  # Accumulate loss
        _, predicted = torch.max(outputs, 1)  # Get the predicted labels
        total += labels.size(0)  # Accumulate the total number of labels
        correct += (predicted == labels).sum().item()  # Count correct predictions

    # Compute average training loss and accuracy
    train_loss = running_loss / len(train_loader)
    train_accuracy = correct / total
    return train_loss, train_accuracy

# Define testing function
def validate(model, val_loader, criterion, device):
    """
    Function to validate the trained model on the validation dataset.

    Args:
        model: The trained neural network model.
        val_loader: DataLoader for the validation dataset.
        criterion: Loss function to compute the validation loss.
        device: Device (CPU or GPU) where the data will be loaded.

    Returns:
        val_loss: Average validation loss.
        val_accuracy: Accuracy of the model on the validation dataset.
    """
    model.eval()  # Set the model to evaluation mode
    running_loss = 0.0
    correct = 0
    total = 0

    # Disable gradient calculation during validation
    with torch.no_grad():
        # Iterate over the batches in the validation DataLoader
        for inputs, labels in val_loader:
            inputs, labels = inputs.to(device), labels.to(device)
            outputs = model(inputs)  # Forward pass
            loss = criterion(outputs, labels)  # Compute the loss
            running_loss += loss.item()  # Accumulate loss
            _, predicted = torch.max(outputs, 1)  # Get the predicted labels
            total += labels.size(0)  # Accumulate the total number of labels
            correct += (predicted == labels).sum().item()  # Count correct predictions

    # Compute average validation loss and accuracy
    val_loss = running_loss / len(val_loader)
    val_accuracy = correct / total
    return val_loss, val_accuracy

def arguments(num_filters, batch_size, activation, filter_organization, batch_normalization, data_augmentation, dropout_value, num_neurons, lr, num_epochs, train_data_folder):
    """
    Function to define and train the CNN model based on the provided arguments.

    Args:
        num_filters (int): Number of filters in the convolutional layers.
        batch_size (int): Batch size for training.
        activation (str): Activation function to be used in the CNN architecture.
        filter_organization (str): Organization pattern for the convolutional filters ('same', 'double', 'halve').
        batch_normalization (str): Whether to use batch normalization ('Yes' or 'No').
        data_augmentation (str): Whether to apply data augmentation ('Yes' or 'No').
        dropout_value (float): Dropout probability value.
        num_neurons (int): Number of neurons in the fully connected layer.
        lr (float): Learning rate for the optimizer.
        num_epochs (int): Number of epochs for training.
    """
    # Set random seed
    torch.manual_seed(42)

    # Set device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # # Path to the training data folder
    # train_data_folder = '/kaggle/input/inaturalist/inaturalist_12K/train'

    # Load the training dataset
    train_dataset = datasets.ImageFolder(root=train_data_folder)

    # Model parameters
    input_channels = 3
    num_classes = len(train_dataset.classes)
    filter_size = 3

    # Convert batch normalization and data augmentation values to boolean
    batch_normalization_val = (batch_normalization == "Yes")
    data_augmentation_val = (data_augmentation == "Yes")

    # Load training and validation data loaders
    train_loader, val_loader = data_loader(train_data_folder, batch_size, data_augmentation_val)

    # Create an instance of the CNN model
    model = CNN(input_channels, num_classes, num_filters, filter_organization, filter_size, activation, batch_normalization_val, dropout_value, num_neurons).to(device)

    # Loss function and optimizer
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr)

    # Training loop
    for epoch in range(num_epochs):
        # Initialize tqdm progress bars for training and validation
        train_progress = tqdm(train_loader, desc=f'Epoch {epoch+1}/{num_epochs} - Training', leave=False)

        # Train the model
        train_loss, train_accuracy = train(model, train_loader, optimizer, criterion, device)

        # Validation loop
        val_loss, val_accuracy = validate(model, val_loader, criterion, device)

        # Log metrics to Weights & Biases
        wandb.log({
            "Epoch": epoch + 1,
            "Train_Accuracy": train_accuracy,
            "Train_Loss": train_loss,
            "Val_Accuracy": val_accuracy,
            "Val_Loss": val_loss
        })

        # Print epoch results
        print(f"Epoch {epoch+1}/{num_epochs},\n Train Loss: {train_loss:.4f}, Train Accuracy: {train_accuracy:.4f},\n Val Loss: {val_loss:.4f}, Val Accuracy: {val_accuracy:.4f}")

"""# Question 4"""

# Define testing function
def test(model, test_loader, criterion, device):
    """
    Function to evaluate the model on a test dataset.

    Args:
        model (torch.nn.Module): The trained model.
        test_loader (torch.utils.data.DataLoader): DataLoader for the test dataset.
        criterion: The loss criterion used for evaluation.
        device (torch.device): Device on which to perform the evaluation.

    Returns:
        test_loss (float): Average loss over the test dataset.
        test_accuracy (float): Accuracy over the test dataset.
    """
    # Set the model to evaluation mode
    model.eval()

    # Initialize variables for loss and accuracy calculation
    running_loss = 0.0
    correct = 0
    total = 0

    # Disable gradient calculation during inference
    with torch.no_grad():
        # Iterate over the test dataset
        for inputs, labels in test_loader:
            inputs, labels = inputs.to(device), labels.to(device)
            # Forward pass
            outputs = model(inputs)
            # Calculate loss
            loss = criterion(outputs, labels)
            running_loss += loss.item()
            # Calculate accuracy
            _, predicted = torch.max(outputs, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

    # Calculate average loss and accuracy
    test_loss = running_loss / len(test_loader)
    test_accuracy = correct / total

    return test_loss, test_accuracy

import matplotlib.pyplot as plt
import numpy as np


def plotgridimage(best_model, test_loader, classes):
    """
    Function to plot sample predictions of the model on the test dataset.

    Args:
        best_model (torch.nn.Module): The trained model to evaluate.
        test_loader (torch.utils.data.DataLoader): DataLoader for the test dataset.
        classes (list): List of class names.

    Returns:
        None
    """
    def imshow_grid(images, actual_labels, predicted_labels, title):
        """
        Function to display a grid of sample images with their actual and predicted labels.

        Args:
            images (torch.Tensor): Tensor containing images.
            actual_labels (list): List of actual class labels.
            predicted_labels (list): List of predicted class labels.
            title (str): Title for the plot.

        Returns:
            None
        """
        # Create subplots
        fig, axs = plt.subplots(10, 3, figsize=(12, 40))

        # Iterate over images and corresponding labels
        for i, ax in enumerate(axs.flat):
            ax.imshow(np.transpose(images[i].numpy(), (1, 2, 0)))

            # Set title with actual and predicted labels
            if actual_labels[i] == predicted_labels[i]:
                actual_color = 'green'
                predicted_color = 'green'
            else:
                actual_color = 'red'
                predicted_color = 'red'

            ax.set_title(f'Actual: {actual_labels[i]} \nPredicted: {predicted_labels[i]}', color=predicted_color, fontsize=15)
            ax.axis('off')

        # Adjust layout and save the plot
        plt.tight_layout(pad=3.0)
        plt.savefig("Sample_Predictions.png")
        # Log the plot to Weights & Biases
        wandb.log({title: [wandb.Image("Sample_Predictions.png")]})
        plt.show()
        plt.close()

    def evaluate_model(model, test_loader, classes):
        """
        Function to evaluate the model on the test dataset and plot sample predictions.

        Args:
            model (torch.nn.Module): The trained model to evaluate.
            test_loader (torch.utils.data.DataLoader): DataLoader for the test dataset.
            classes (list): List of class names.

        Returns:
            None
        """
        model.eval()
        class_images = {cls: [] for cls in classes}
        actual_labels = []
        predicted_labels = []
        images_shown = 0

        with torch.no_grad():
            for images, labels in test_loader:
                images, labels = images.to(device), labels.to(device)
                outputs = model(images)
                _, predicted = torch.max(outputs, 1)

                for i in range(len(labels)):
                    label = labels[i].item()
                    predicted_label = predicted[i].item()

                    class_name = classes[label]

                    if len(class_images[class_name]) < 3:
                        class_images[class_name].append(images[i].cpu())
                        actual_labels.append(classes[label])
                        predicted_labels.append(classes[predicted_label])
                        images_shown += 1

                    if images_shown >= 10 * 3:
                        images_to_show = torch.stack([img for sublist in class_images.values() for img in sublist[:3]])
                        actual_labels_to_show = actual_labels[:30]
                        predicted_labels_to_show = predicted_labels[:30]

                        # Call imshow_grid to display the sample predictions
                        imshow_grid(images_to_show, actual_labels_to_show, predicted_labels_to_show, 'Sample Predictions')
                        return

    # Check device availability
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    # Call evaluate_model to generate and display sample predictions
    evaluate_model(best_model, test_loader, classes)

def arguments_2(num_filters, batch_size, activation, filter_organization, batch_normalization,
                data_augmentation, dropout_value, num_nuerons, lr, num_epochs,train_data_folder,test_data_folder):
    """
    Function to define and execute the training process for the model with specified hyperparameters.

    Args:
        num_filters (int): Number of filters in the convolutional layers.
        batch_size (int): Batch size for training and testing.
        activation (str): Activation function for the convolutional layers.
        filter_organization (str): Strategy for adjusting the number of filters.
        batch_normalization (str): Whether to use batch normalization.
        data_augmentation (str): Whether to apply data augmentation.
        dropout_value (float): Dropout value for the model.
        num_nuerons (int): Number of neurons in the dense layer.
        lr (float): Learning rate for optimization.
        num_epochs (int): Number of epochs for training.

    Returns:
        None
    """
    # Set random seed
    torch.manual_seed(42)

    # Set device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Define data transformations for training and testing without augmentation
    without_augmentation_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
    ])

    # # Define the folder paths for training and testing datasets
    # train_data_folder = '/kaggle/input/inaturalist/inaturalist_12K/train'
    # test_data_folder = '/kaggle/input/inaturalist/inaturalist_12K/val'

    # Load training and testing datasets
    train_dataset = datasets.ImageFolder(root=train_data_folder)
    test_dataset = datasets.ImageFolder(root=test_data_folder, transform=without_augmentation_transform)

    # Model parameters
    input_channels = 3
    num_classes = len(train_dataset.classes)
    filter_size = 3

    # Convert batch_normalization and data_augmentation strings to boolean values
    batch_normalization_val = True if batch_normalization == "Yes" else False
    data_augmentation_val = True if data_augmentation == "Yes" else False

    # Load training data using data_loader function
    train_loader, _ = data_loader(train_data_folder, batch_size, data_augmentation_val)

    # Load testing data using DataLoader
    test_loader = DataLoader(dataset=test_dataset, batch_size=batch_size, shuffle=True)

    # Get the class labels from the test dataset
    classes = test_dataset.classes

    # Create model instance
    best_model = CNN(input_channels, num_classes, num_filters, filter_organization, filter_size,
                     activation, batch_normalization_val, dropout_value, num_nuerons).to(device)

    # Loss function and optimizer
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(best_model.parameters(), lr)

    # Train the model for the specified number of epochs
    for epoch in tqdm(range(num_epochs), desc='Training', leave=False):
        epoch_progress = tqdm(test_loader, desc=f'Epoch {epoch+1}/{num_epochs}', leave=False)
        train_loss, train_accuracy = train(best_model, train_loader, optimizer, criterion, device)
        test_loss, test_accuracy = test(best_model, test_loader, criterion, device)

        # Log test metrics to Weights & Biases
        wandb.log({
            "Epoch": epoch + 1,
            "Train_Accuracy": train_accuracy,
            "Train_Loss": train_loss,
            "Test_Accuracy": test_accuracy,
            "Test_Loss": test_loss
        })

        # Print test loss and accuracy
        print(f'Test Loss: {test_loss}')
        print(f'Test Accuracy: {test_accuracy}')

    # Plot sample predictions
    plotgridimage(best_model, test_loader, classes)

import argparse
import wandb
wandb.login()





DEFAULT_HYPERPARAMETERS = {
    'num_filters': [128],
    'activation': ['gelu'],
    'filter_organization': ['double'],
    'batch_normalization': ['Yes'],
    'dropout_value': [0.3],
    'learning_rate': [0.0001],
    'num_epochs': [10],
    'dense_neurons': [1024],
    'batch_size': [32],
    'data_augmentation': ['Yes'],
    'wandb_project': 'DL_Assignment_2_CS23M046',
    'wandb_entity': 'cs23m046',
    'train_dataset': None,
    'test_dataset': None,
    'mode': 'Training-Validation'
}

def main():
    parser = argparse.ArgumentParser(description="Neural Network Configuration Parameters")

    parser.add_argument("--num_filters", type=int, nargs='+', default=DEFAULT_HYPERPARAMETERS['num_filters'], help="Number of filters/kernels in each convolutional layer")
    parser.add_argument("--activation", type=str, nargs='+', default=DEFAULT_HYPERPARAMETERS['activation'], help="Activation function after each layer")
    parser.add_argument("--filter_organization", type=str, nargs='+', default=DEFAULT_HYPERPARAMETERS['filter_organization'], help="Filter organization pattern")
    parser.add_argument("--batch_normalization", type=str, nargs='+', default=DEFAULT_HYPERPARAMETERS['batch_normalization'], help="Whether to apply batch normalization")
    parser.add_argument("--dropout_value", type=float, nargs='+', default=DEFAULT_HYPERPARAMETERS['dropout_value'], help="Dropout rate to prevent overfitting")
    parser.add_argument("--learning_rate", type=float, nargs='+', default=DEFAULT_HYPERPARAMETERS['learning_rate'], help="Learning rate for model training")
    parser.add_argument("--num_epochs", type=int, nargs='+', default=DEFAULT_HYPERPARAMETERS['num_epochs'], help="Number of epochs for training")
    parser.add_argument("--dense_neurons", type=int, nargs='+', default=DEFAULT_HYPERPARAMETERS['dense_neurons'], help="Number of neurons in the fully connected layer")
    parser.add_argument("--batch_size", type=int, nargs='+', default=DEFAULT_HYPERPARAMETERS['batch_size'], help="Batch size for training data")
    parser.add_argument("--data_augmentation", type=str, nargs='+', default=DEFAULT_HYPERPARAMETERS['data_augmentation'], help="Whether to apply data augmentation")
    parser.add_argument("--wandb_project", type=str, default=DEFAULT_HYPERPARAMETERS['wandb_project'], help="Project name used to track experiments in Weights & Biases dashboard")
    parser.add_argument("--wandb_entity", type=str, default=DEFAULT_HYPERPARAMETERS['wandb_entity'], help="Wandb Entity used to track experiments in the Weights & Biases dashboard.")
    parser.add_argument("--train_dataset", type=str, default=DEFAULT_HYPERPARAMETERS['train_dataset'], help="Path to training dataset")
    parser.add_argument("--test_dataset", type=str, default=DEFAULT_HYPERPARAMETERS['test_dataset'], help="Path to test dataset")
    parser.add_argument("--mode", type=str, default=DEFAULT_HYPERPARAMETERS['mode'], choices=["Training-Validation", "Testing"], help="Mode of operation")

    args = parser.parse_args()

    # Extracting individual hyperparameters
    num_filters = args.num_filters[0]
    activation = args.activation[0]
    filter_organization = args.filter_organization[0]
    batch_normalization = args.batch_normalization[0]
    dropout_value = args.dropout_value[0]
    learning_rate = args.learning_rate[0]
    num_epochs = args.num_epochs[0]
    dense_neurons = args.dense_neurons[0]
    batch_size = args.batch_size[0]
    data_augmentation = args.data_augmentation[0]
    wandb_project = args.wandb_project
    wandb_entity = args.wandb_entity
    train_dataset = args.train_dataset
    test_dataset = args.test_dataset
    mode = args.mode

    # Initialize wandb
    wandb.init(project=wandb_project, entity=wandb_entity)
    run_name = f"activation_{activation}_num_filters_{num_filters}_dense_{dense_neurons}_lr_{learning_rate}"
    wandb.run.name = run_name

    if mode == "Training-Validation":
        arguments(num_filters, batch_size, activation, filter_organization, batch_normalization, data_augmentation,
                  dropout_value, dense_neurons, learning_rate, num_epochs, train_dataset)

    elif mode == "Testing":
        arguments_2(num_filters, batch_size, activation, filter_organization, batch_normalization, data_augmentation, dropout_value, dense_neurons, learning_rate, num_epochs, train_dataset, test_dataset)


    wandb.finish()

if __name__ == "__main__":
    main()
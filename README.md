# HexaHunt

A case study project on AI game development by **Frilles, Roljohn C.**, **Macaraeg, Paul Angelo O.**, **Manansala, Roan P.**, and **Manucom, Precious Grace Deborah S.**

## Overview

HexaHunt is a strategic board game inspired by Dots and Boxes, played on a hexagonal grid. Players take turns drawing lines between points, with the goal of completing hexagons to claim them. The game features an intelligent AI opponent powered by the Minimax algorithm with Alpha-Beta pruning.

## Features

- **Hexagonal Game Board**: A unique twist on the classic Dots and Boxes game
- **Intelligent AI Opponent**: 
  - Minimax algorithm with Alpha-Beta pruning
  - Configurable difficulty levels
  - Move ordering optimization
  - Transposition table for cached positions
- **Visualization System**:
  - Optional real-time stats display showing AI thinking metrics
  - Visual highlighting of AI's evaluation process
  - Color-coding for different evaluation states
  - Toggle button to show/hide technical details
- **Interactive UI**:
  - Main menu with multiple options
  - How to play guide
  - About section
  - Settings configuration
  - Seamless navigation between game and menu
- **Customization Options**:
  - Adjustable board size (radius 1-4)
  - Configurable AI difficulty (Easy, Medium, Hard)
- **Responsive Design**:
  - Dynamic scaling of game elements based on window size
  - Persistent UI across different screen dimensions
  - Properly centered game board regardless of window dimensions

## Implemented Algorithms

- **Minimax Algorithm**: AI decision-making framework that evaluates possible moves by exploring the game tree
- **Alpha-Beta Pruning**: Optimization technique that reduces the number of nodes evaluated in the search tree
- **Transposition Tables**: Memory-efficient caching system for storing previously evaluated game positions
- **Move Ordering**: Heuristic technique to examine most promising moves first, improving pruning efficiency

## Date Created

This project was developed for the Introduction to Artificial Intelligence subject at the Polytechnic University of the Philippines during the Second Semester (April to June) of Academic Year 2024-2025.

## How to Run

To run HexaHunt locally, follow these steps:

1. **Ensure Python is installed**
   ```bash
   python --version  # Should be Python 3.6 or higher
   ```

2. **Install required dependencies**
   ```bash
   pip install pygame
   ```

3. **Clone the repository or download the source code**
   ```bash
   git clone https://github.com/PaullyMac/HexaHunt.git
   cd HexaHunt
   ```

4. **Run the game**
   ```bash
   python main.py
   ```

## Technologies Used

- **Python 3**: Core programming language
- **Pygame**: Game development library for graphics and input handling

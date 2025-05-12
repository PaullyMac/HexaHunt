# Changelog

## May 12, 2025

### Fixed
- Fixed critical game state preservation during window resize - player moves, scores, and turn states are now properly maintained
- Enhanced edge mapping algorithm to properly translate edge positions between different window sizes
- Fixed issue where AI would sometimes attempt to play on already claimed edges
- Improved validity checks throughout the minimax algorithm to ensure only valid moves are considered
- Enhanced transposition table logic to verify cached moves are still valid in the current game state

## May 5, 2025

### Added
- Added custom application icon using logo.png
- Added logo image to About screen
- Added clickable GitHub links for all developers in About screen
- Added detailed treasure and artifact descriptions in the How to Play screen
- Added scrollable content for the How to Play screen to accommodate all game information
- Added structured tables for treasures and artifacts with descriptions and point values

### Fixed
- Fixed initialization issues with CURRENT_HEIGHT variable
- Fixed function ordering to ensure initialize_hexagons is defined before it's called
- Fixed overlapping text in How to Play screen by increasing column spacing
- Fixed shadow effect on text that was causing a "double font" appearance

### Improved
- Center-aligned text in About and How to Play screens for better visual appearance
- Improved table formatting with clear column headers and horizontal separator lines
- Enhanced scrolling experience in How to Play screen with mouse wheel support
- Made all sections in How to Play screen properly structured and readable
- Optimized spacing between columns in treasure and artifact tables
- Made the How to Play title scroll with the content for better contextual navigation

## May 4, 2025

### Added
- Added a back button to the game screen that allows players to return to the main menu during gameplay
- Implemented proper drawing of the back button with hover effects
- Added button positioning that scales appropriately with window size
- Added "Show Stats" button to toggle visibility of AI performance metrics during gameplay
- Added ability to hide/show AI statistics to reduce visual clutter

### Fixed
- Fixed game logic issue where human player wasn't gaining points when completing hexagons
- Fixed issue where AI could attempt to play on already filled edges
- Added validation in minimax algorithm to ensure only valid moves are considered
- Added additional safeguards in the AI move selection process
- Fixed debug output to properly track score changes
- Fixed stats display position to avoid overlapping with the "Show Stats" button
- Fixed game board positioning to ensure it's properly centered in the GUI

### Improved
- Center-aligned text in About screen for better visual appearance
- Enhanced validation throughout the move application process
- Improved error handling for edge cases
- Implemented cleaner UI with optional stats display that doesn't clutter the game interface
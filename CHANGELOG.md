# Changelog

## May 4, 2025

### Added
- Added a back button to the game screen that allows players to return to the main menu during gameplay
- Implemented proper drawing of the back button with hover effects
- Added button positioning that scales appropriately with window size

### Fixed
- Fixed game logic issue where human player wasn't gaining points when completing hexagons
- Fixed issue where AI could attempt to play on already filled edges
- Added validation in minimax algorithm to ensure only valid moves are considered
- Added additional safeguards in the AI move selection process
- Fixed debug output to properly track score changes

### Improved
- Center-aligned text in About screen for better visual appearance
- Enhanced validation throughout the move application process
- Improved error handling for edge cases
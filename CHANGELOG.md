# Changelog

## June 16, 2025

### Added
- **Artifact Hint System**: Implemented visual hints for artifact usage
  - Added `draw_artifact_hint()` function to display usage instructions at bottom center of screen
  - Hints appear when artifacts are claimed and persist for 5 seconds
  - Added timer system (`artifact_hint_timer`) to manage hint display duration
  - Integrated hint display into the main drawing pipeline

### Fixed
- **Artifact Hint Display Issues**: Resolved multiple problems preventing artifact hints from appearing
  - Fixed variable scope issues where `artifact_hint` variables weren't properly passed between functions
  - Updated `draw_board()` function signature to accept artifact hint parameters
  - Corrected all `draw_board()` function calls throughout the codebase to pass hint parameters
  - Fixed wrong hint assignments (compass hint was being assigned to gauntlet)
  - Removed duplicate/overwriting hint assignments that were clearing hints immediately
  - Fixed drawing order issue where hints were drawn after `pygame.display.flip()` was called

- **Game Over Text Positioning**: Fixed game over message positioning
  - Implemented proper centering using `get_rect(center=...)` method
  - Added semi-transparent overlay for better text visibility over game board
  - Added text shadow and dynamic coloring based on winner (Blue for human, Red for AI, Black for tie)
  - Positioned text below center of window for better visual placement

- **Compass Message Character Encoding**: Fixed character encoding issue in compass usage message

### Improved
- **Artifact Hint Visibility**: Enhanced visual presentation of artifact hints
  - Added semi-transparent white background with purple border for better readability
  - Used distinctive purple text color to differentiate from other UI elements
  - Positioned hints at bottom center with proper padding and styling
  - Made hints non-intrusive while still clearly visible

- **Game Over Screen**: Enhanced end-game presentation
  - Added larger, more prominent game over text
  - Improved text contrast with shadow effects and background overlay
  - Better visual hierarchy for end-game information

- **Code Organization**: Improved function parameter consistency
  - Standardized `draw_board()` function calls across all game states
  - Better separation of concerns between drawing and game logic
  - Enhanced maintainability of the drawing pipeline

### Technical Details
- **Artifact Hints Now Display**:
  - "Press the 'G' key to activate the gauntlet" - when Shadow Gauntlet is claimed
  - "Press the 'C' key. Click on any opponent-owned hexagon" - when Compass of Portals is claimed  
  - "You get a bonus turn credit" - when Hourglass of Quickening is claimed
- **Function Signatures Updated**: All `draw_board()` calls now properly pass `artifact_hint` and `artifact_hint_timer` parameters
- **Drawing Pipeline**: Hints are now rendered before the final `pygame.display.flip()` call

## June 9, 2025

### Fixed
- Fixed board centering issue where hex grid was positioned in the top-left corner instead of screen center
- Implemented dynamic board positioning that centers the hex grid regardless of board radius (1-4) and AI depth (2-4)
- Added proper margin calculations for UI elements (logo at top, scores at bottom, buttons on sides)
- Fixed board positioning persistence during window resizing - hex grid now stays centered when zooming in/out
- Enhanced window resize handling to preserve game state while repositioning board to center
- Improved edge mapping algorithm during resize to maintain all player moves and game progress

### Improved
- Board now dynamically centers itself based on actual board dimensions rather than fixed offsets
- Enhanced responsive design - hex grid automatically adjusts position for different window sizes
- Improved visual layout by ensuring proper spacing between board and UI elements
- Better user experience with consistent board centering across all game configurations

## May 13, 2025

### Improved
- Replaced text title "HexaHunt" with a custom logo image in the main menu
- Increased logo size for better visibility and visual appeal
- Added error handling with text fallback if logo image fails to load
- Increased spacing between logo and subtitle text for improved layout
- Enhanced visual identity by implementing graphical elements instead of text
- Increased hexagonal grid size for better visibility on all board sizes
- Dynamically scaled hexagons based on board radius to optimize display
- Fixed gradient rendering in background by adding missing parameters
- Ensured hexagons are properly connected with no gaps between cells
- Improved board positioning and centering for all window sizes

## May 12, 2025

### Fixed
- Fixed critical game state preservation during window resize - player moves, scores, and turn states are now properly maintained
- Enhanced edge mapping algorithm to properly translate edge positions between different window sizes
- Fixed issue where AI would sometimes attempt to play on already claimed edges
- Improved validity checks throughout the minimax algorithm to ensure only valid moves are considered
- Enhanced transposition table logic to verify cached moves are still valid in the current game state

### Improved
- Reduced animation image size to prevent overlapping with the hexagonal grid
- Repositioned "AI is thinking" animation to appear at the bottom of the screen
- Enhanced AI move selection with more robust validation to prevent duplicate moves
- Added extra safeguards to prevent minimax from considering or returning invalid moves
- Improved error handling and diagnostic messages for debugging AI move selection

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
# Project Roadmap

## UI/UX Improvements
- [ ] **Remove Overlay**: Explore ways to display translation bubbles without a full-screen overlay, or make the overlay completely transparent/click-through when not selecting.
- [ ] **Improve Bubble Positioning**: Further refine the positioning logic to ensure bubbles don't overlap or go off-screen, and align perfectly with the source text.
- [ ] **Change Spinner Color**: Update the loading spinner color from blue to "blood red" (#8a0303) to match the desired aesthetic.

## Core Functionality & Performance
- [ ] **Optimize Text Recognition**: 
    - Investigate advanced PaddleOCR parameters for better accuracy.
    - Consider preprocessing images (contrast, binarization) before OCR.
- [ ] **Optimize Translation Performance**:
    - Implement caching for repeated phrases.
    - Explore faster translation APIs or local models if feasible.
    - Optimize the threading/pipeline to reduce latency.

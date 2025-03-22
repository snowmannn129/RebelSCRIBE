# initialize

**API Version:** 1.0.0

**Component:** RebelCAD

Graphics system for RebelCAD.

The GraphicsSystem class manages the graphics subsystem of RebelCAD,
including window creation, rendering context setup, and frame rendering.
It supports multiple graphics APIs and follows the singleton pattern.
/
class GraphicsSystem {
public:
    /**

## Parameters

- **api**: The graphics API to use.
- **props**: The window properties.

## Returns

: Reference to the GraphicsSystem instance.
/
    static GraphicsSystem& getInstance();

    /**

## Exceptions

- **Error**: If initialization fails.


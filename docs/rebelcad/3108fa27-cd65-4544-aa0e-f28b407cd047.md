# GraphicsSystem

**API Version:** 1.0.0

**Component:** RebelCAD

Supported graphics APIs. Properties for the application window. Constructs a new WindowProperties object. Graphics system for RebelCAD.

enum: GraphicsAPI
This enum defines the graphics APIs that can be used by the GraphicsSystem.
/
enum class GraphicsAPI {
    OpenGL,     ///< OpenGL API
    Vulkan,     ///< Vulkan API
    DirectX11,  ///< DirectX 11 API
    DirectX12   ///< DirectX 12 API
};
/**
struct: WindowProperties
This struct defines the properties of the application window,
including title, dimensions, and display settings.
/
struct WindowProperties {
    std::string title;  ///< Window title
    int width;          ///< Window width in pixels
    int height;         ///< Window height in pixels
    bool fullscreen;    ///< Fullscreen mode flag
    bool vsync;         ///< Vertical sync flag
    /**
/
    WindowProperties(
        const std::string& title = "RebelCAD",
        int width = 1280,
        int height = 720,
        bool fullscreen = false,
        bool vsync = true
    ) : title(title), width(width), height(height), fullscreen(fullscreen), vsync(vsync) {}
};
/**
class: GraphicsSystem
The GraphicsSystem class manages the graphics subsystem of RebelCAD,
including window creation, rendering context setup, and frame rendering.
It supports multiple graphics APIs and follows the singleton pattern.

## Parameters

- **title**: Window title
- **width**: Window width in pixels
- **height**: Window height in pixels
- **fullscreen**: Fullscreen mode flag
- **vsync**: Vertical sync flag


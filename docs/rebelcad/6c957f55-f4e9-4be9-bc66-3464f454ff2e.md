# GraphicsSystem

**API Version:** 1.0.0

**Component:** RebelCAD

Supported graphics APIs.

This enum defines the graphics APIs that can be used by the GraphicsSystem.
/
enum class GraphicsAPI {
    OpenGL,     ///< OpenGL API
    Vulkan,     ///< Vulkan API
    DirectX11,  ///< DirectX 11 API
    DirectX12   ///< DirectX 12 API
};

/**

## Parameters

- **title**: Window title
- **width**: Window width in pixels
- **height**: Window height in pixels
- **fullscreen**: Fullscreen mode flag
- **vsync**: Vertical sync flag
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


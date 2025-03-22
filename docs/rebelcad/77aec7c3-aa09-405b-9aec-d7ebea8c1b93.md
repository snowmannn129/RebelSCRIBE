# BooleanTool

**API Version:** 1.0.0

**Component:** RebelCAD

Enum defining the type of boolean operation Parameters for configuring a boolean operation Tool for performing boolean operations between solid bodies

/
enum class BooleanOperationType {
    Union,      ///< Combine two bodies, keeping all material
    Subtract,   ///< Remove second body from first body
    Intersect   ///< Keep only material common to both bodies
};
/**
/
struct BooleanParams {
    BooleanOperationType operation_type = BooleanOperationType::Union;
    bool maintain_features = true;  ///< Try to maintain feature edges/faces
    float intersection_tolerance = 1e-6f;  ///< Tolerance for intersection detection
    bool optimize_result = true;    ///< Optimize resulting mesh
    int max_refinement_steps = 3;   ///< Maximum mesh refinement iterations
};
/**
class: BooleanTool
The BooleanTool performs boolean operations (union, subtract, intersect)
between two solid bodies. It handles mesh intersection detection, topology
management, and proper handling of normals and UV coordinates.


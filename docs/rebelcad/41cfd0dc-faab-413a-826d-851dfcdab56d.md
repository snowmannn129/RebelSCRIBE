# GenerateGeometry

**API Version:** 1.0.0

**Component:** RebelCAD

Evaluate curve derivative at parameter value

/**

## Parameters

- **t**: Parameter value in range [0,1]
- **order**: Derivative order (1 = first derivative, etc.)
- **segments**: Number of segments for discretization

## Returns

: Vector of derivative values
/
    std::vector<glm::vec3> EvaluateDerivatives(float t, int order) const;

    /**


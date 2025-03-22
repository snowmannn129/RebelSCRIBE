# calculateCurvature

**API Version:** 1.0.0

**Component:** RebelCAD

Get the current control points

/**

## Parameters

- **minPoints**: Minimum number of points to generate (default: 50)
- **maxPoints**: Maximum number of points to generate (default: 500)
- **curvatureTolerance**: Tolerance for adaptive sampling (default: 0.1)
- **u**: Parameter value between 0 and 1

## Returns

: Vector of control point coordinates
/
    const std::vector<std::pair<double, double>>& getControlPoints() const;

    /**


# Error

**API Version:** 1.0.0

**Component:** RebelCAD

Error codes for RebelCAD. Exception class for RebelCAD errors.

enum: ErrorCode
This enum defines the error codes that can be used to identify
different types of errors in the RebelCAD application.
/
enum class ErrorCode {
    None = 0,                 ///< No error
    Unknown,                  ///< Unknown error
    InvalidArgument,          ///< Invalid argument provided to a function
    InvalidOperation,         ///< Invalid operation attempted
    OutOfMemory,              ///< Out of memory error
    FileNotFound,             ///< File not found error
    FileIOError,              ///< File I/O error
    ShaderCompilationFailed,  ///< Shader compilation failed
    GraphicsError,            ///< Graphics system error
    SystemError               ///< System error
    // Add more error codes as needed
};
/**
class: Error
The Error class is used to represent errors that occur in the RebelCAD
application. It extends std::runtime_error and adds additional information
such as an error code, file name, and line number.


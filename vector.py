# vector.py

# built-in 

""" Inventory [ Math ] { Python Built-in Library }
1. math.sqrt(x) ; Returns the square root of x.
2. math.pow(x, y) ; Returns x raised to the power of y (x^y) as a float.
3. math.exp(x) ; Returns e raised to the power of x.
4. math.log(x) ; Returns the natural logarithm of x (base e).
5. math.log(x, base) ; Returns the logarithm of x to the specified base.
6. math.log10(x) ; Returns the base-10 logarithm of x.
7. math.log2(x) ; Returns the base-2 logarithm of x.
8. math.floor(x) ; Returns the largest integer less than or equal to x.
9. math.ceil(x) ; Returns the smallest integer greater than or equal to x.
10. math.trunc(x) ; Truncates x to the nearest integer toward zero.
11. math.fabs(x) ; Returns the absolute value of x as a float.
12. math.factorial(x) ; Returns the factorial of x (x!).
13. math.gcd(a, b) ; Returns the greatest common divisor of a and b.
14. math.lcm(a, b) ; Returns the least common multiple of a and b (Python 3.9+).
15. math.isclose(a, b, rel_tol=1e-09, abs_tol=0.0) ; Checks if a and b are close in value.
16. math.sin(x) ; Returns the sine of x (x in radians).
17. math.cos(x) ; Returns the cosine of x (x in radians).
18. math.tan(x) ; Returns the tangent of x (x in radians).
19. math.asin(x) ; Returns the arcsine of x in radians.
20. math.acos(x) ; Returns the arccosine of x in radians.
21. math.atan(x) ; Returns the arctangent of x in radians.
22. math.atan2(y, x) ; Returns atan(y/x) in radians, accounting for quadrant.
23. math.radians(x) ; Converts angle x from degrees to radians.
24. math.degrees(x) ; Converts angle x from radians to degrees.
25. math.hypot(x, y) ; Returns the Euclidean norm √(x² + y²).
26. math.copysign(x, y) ; Returns x with the sign of y.
27. math.fmod(x, y) ; Returns the remainder of x/y (same sign as x).
28. math.remainder(x, y) ; Returns IEEE 754-style remainder of x with respect to y.
29. math.frexp(x) ; Returns (m, e) such that x = m * 2**e and m is in [0.5, 1).
30. math.ldexp(m, e) ; Returns m * 2**e (inverse of frexp).
31. math.modf(x) ; Returns fractional and integer parts of x as a tuple.
32. math.pi ; Mathematical constant π (3.14159...).
33. math.e ; Mathematical constant e (2.71828...).
34. math.tau ; Mathematical constant τ (2π).
35. math.inf ; Floating-point positive infinity.
36. math.nan ; Floating-point NaN (Not a Number).
"""
import math

from typing import Union, List
import numbers

Vector = Union[list, tuple]

def is_vector(v: Vector) -> bool:
    """Check if input is a valid vector (list or tuple of numbers)."""
    if not isinstance(v, (list, tuple)):
        return False
    return all(isinstance(x, numbers.Number) for x in v) and len(v) > 0

def shape_match(v1: Vector, v2: Vector) -> bool:
    """Check if two vectors have the same length."""
    if not (is_vector(v1) and is_vector(v2)):
        return False
    return len(v1) == len(v2)

def round_vector(v: Vector, decimals: int = 3) -> Vector:
    """Round all elements of a vector to specified decimal places."""
    if not is_vector(v):
        raise ValueError("Input must be a valid vector")
    return type(v)(round(x, decimals) for x in v)

def add(v1: Vector, v2: Vector) -> Vector:
    """Add two vectors element-wise."""
    if not shape_match(v1, v2):
        raise ValueError("Vectors must have the same shape")
    return type(v1)(x + y for x, y in zip(v1, v2))

def subtract(v1: Vector, v2: Vector) -> Vector:
    """Subtract v2 from v1 element-wise."""
    if not shape_match(v1, v2):
        raise ValueError("Vectors must have the same shape")
    return type(v1)(x - y for x, y in zip(v1, v2))

def scalar_multiply(scalar: float, v: Vector) -> Vector:
    """Multiply a vector by a scalar."""
    if not is_vector(v):
        raise ValueError("Input must be a valid vector")
    if not isinstance(scalar, numbers.Number):
        raise ValueError("Scalar must be a number")
    return type(v)(scalar * x for x in v)

def dot(v1: Vector, v2: Vector) -> float:
    """Compute the dot product of two vectors."""
    if not shape_match(v1, v2):
        raise ValueError("Vectors must have the same shape")
    return sum(x * y for x, y in zip(v1, v2))

def magnitude(v: Vector) -> float:
    """Compute the magnitude (Euclidean norm) of a vector."""
    if not is_vector(v):
        raise ValueError("Input must be a valid vector")
    return math.sqrt(sum(x * x for x in v))

def normalize(v: Vector) -> Vector:
    """Normalize a vector to unit length."""
    if not is_vector(v):
        raise ValueError("Input must be a valid vector")
    mag = magnitude(v)
    if mag == 0:
        raise ValueError("Cannot normalize a zero vector")
    return scalar_multiply(1 / mag, v)

def distance(v1: Vector, v2: Vector) -> float:
    """Compute the Euclidean distance between two vectors."""
    if not shape_match(v1, v2):
        raise ValueError("Vectors must have the same shape")
    return magnitude(subtract(v1, v2))

def angle_between(v1: Vector, v2: Vector) -> float:
    """Compute the angle (in radians) between two vectors."""
    if not shape_match(v1, v2):
        raise ValueError("Vectors must have the same shape")
    mag1, mag2 = magnitude(v1), magnitude(v2)
    if mag1 == 0 or mag2 == 0:
        raise ValueError("Cannot compute angle with zero vector")
    cos_theta = dot(v1, v2) / (mag1 * mag2)
    # Handle floating-point errors
    cos_theta = min(1.0, max(-1.0, cos_theta))
    return math.acos(cos_theta)

def project(v1: Vector, v2: Vector) -> Vector:
    """Project v1 onto v2."""
    if not shape_match(v1, v2):
        raise ValueError("Vectors must have the same shape")
    mag2_squared = dot(v2, v2)
    if mag2_squared == 0:
        raise ValueError("Cannot project onto zero vector")
    scalar = dot(v1, v2) / mag2_squared
    return scalar_multiply(scalar, v2)

def cross(v1: Vector, v2: Vector) -> Vector:
    """Compute the cross product of two 3D vectors."""
    if not (is_vector(v1) and is_vector(v2) and len(v1) == 3 and len(v2) == 3):
        raise ValueError("Cross product requires two 3D vectors")
    x = v1[1] * v2[2] - v1[2] * v2[1]
    y = v1[2] * v2[0] - v1[0] * v2[2]
    z = v1[0] * v2[1] - v1[1] * v2[0]
    return type(v1)((x, y, z))

def signed_angle_between(v1: Vector, v2: Vector) -> float:
    """Compute the signed angle (in radians) between two 2D or 3D vectors using the right-hand rule."""
    if not (is_vector(v1) and is_vector(v2)):
        raise ValueError("Inputs must be valid vectors")
    if not shape_match(v1, v2) or len(v1) not in (2, 3):
        raise ValueError("Signed angle requires two 2D or 3D vectors of the same dimension")
    
    # Compute the unsigned angle using the dot product
    mag1, mag2 = magnitude(v1), magnitude(v2)
    if mag1 == 0 or mag2 == 0:
        raise ValueError("Cannot compute angle with zero vector")
    cos_theta = dot(v1, v2) / (mag1 * mag2)
    # Handle floating-point errors
    cos_theta = min(1.0, max(-1.0, cos_theta))
    angle = math.acos(cos_theta)
    
    # Determine the sign using the appropriate cross product
    if len(v1) == 2:
        # 2D case: cross product is a scalar (x1*y2 - y1*x2)
        cross_product = v1[0] * v2[1] - v1[1] * v2[0]
        # Positive: counterclockwise (positive angle); Negative: clockwise (negative angle)
        if cross_product < 0:
            angle = -angle
    else:
        # 3D case: use z-component of the cross product
        cross_product = cross(v1, v2)
        # Positive z: counterclockwise (positive angle); Negative z: clockwise (negative angle)
        if cross_product[2] < 0:
            angle = -angle
    
    return angle

def hadamard(v1: Vector, v2: Vector) -> Vector:
    """Compute the Hadamard (element-wise) product of two vectors."""
    if not shape_match(v1, v2):
        raise ValueError("Vectors must have the same shape")
    return type(v1)(x * y for x, y in zip(v1, v2))

def mean_vector(vectors: List[Vector]) -> Vector:
    """Compute the element-wise mean of a list of vectors."""
    if not vectors or not all(is_vector(v) for v in vectors):
        raise ValueError("Input must be a non-empty list of vectors")
    n = len(vectors)
    if n == 0:
        raise ValueError("Cannot compute mean of empty vector list")
    if not all(len(v) == len(vectors[0]) for v in vectors):
        raise ValueError("All vectors must have the same shape")
    result = vectors[0]
    for v in vectors[1:]:
        result = add(result, v)
    return scalar_multiply(1 / n, result)
    
def lerp(v1: Vector, v2: Vector, t: float) -> Vector:
    """Linearly interpolate between v1 and v2 by factor t (0 <= t <= 1)."""
    if not shape_match(v1, v2):
        raise ValueError("Vectors must have the same shape")
    if not 0 <= t <= 1:
        raise ValueError("Interpolation factor must be between 0 and 1")
    return add(scalar_multiply(1 - t, v1), scalar_multiply(t, v2))
    
def reflect(v: Vector, normal: Vector) -> Vector:
    """Reflect vector v over a normal vector."""
    if not shape_match(v, normal):
        raise ValueError("Vectors must have the same shape")
    return subtract(v, scalar_multiply(2 * dot(v, normal), normalize(normal)))    

def to_spherical(v: Vector) -> tuple:
    """Convert 3D vector to spherical coordinates (r, theta, phi)."""
    if not (is_vector(v) and len(v) == 3):
        raise ValueError("Requires a 3D vector")
    x, y, z = v
    r = magnitude(v)
    theta = math.acos(z / r) if r != 0 else 0
    phi = math.atan2(y, x)
    return r, theta, phi

def compare(v1: Vector, v2: Vector, tolerance: float = 0.1) -> bool:
    """Compare if two vectors are essentially the same within a given tolerance."""
    if not (is_vector(v1) and is_vector(v2)):
        raise ValueError("Inputs must be valid vectors")
    if not shape_match(v1, v2):
        raise ValueError("Vectors must have the same shape")
    if not isinstance(tolerance, numbers.Number) or tolerance < 0:
        raise ValueError("Tolerance must be a non-negative number")
    
    return all(abs(x - y) <= tolerance for x, y in zip(v1, v2))

def compare_distance(v1: Vector, v2: Vector, tolerance: float = 0.1) -> bool:
    """Compare if two vectors are essentially the same based on Euclidean distance."""
    if not (is_vector(v1) and is_vector(v2)):
        raise ValueError("Inputs must be valid vectors")
    if not shape_match(v1, v2):
        raise ValueError("Vectors must have the same shape")
    if not isinstance(tolerance, numbers.Number) or tolerance < 0:
        raise ValueError("Tolerance must be a non-negative number")
    
    return distance(v1, v2) <= tolerance

def rotate_vector(v: Vector, rad: float) -> Vector:
    """Rotate a 2D or 3D vector by an angle (in radians) around the origin (2D) or z-axis (3D)."""
    if not is_vector(v):
        raise ValueError("Input must be a valid vector")
    if len(v) not in (2, 3):
        raise ValueError("Vector must be 2D or 3D")
    if not isinstance(rad, numbers.Number):
        raise ValueError("Rotation angle must be a number")
    
    cos_theta = math.cos(rad)
    sin_theta = math.sin(rad)
    
    if len(v) == 2:
        # 2D rotation: [x' = x*cos - y*sin, y' = x*sin + y*cos]
        x, y = v
        x_new = x * cos_theta - y * sin_theta
        y_new = x * sin_theta + y * cos_theta
        return type(v)((x_new, y_new))
    else:
        # 3D rotation around z-axis: [x' = x*cos - y*sin, y' = x*sin + y*cos, z' = z]
        x, y, z = v
        x_new = x * cos_theta - y * sin_theta
        y_new = x * sin_theta + y * cos_theta
        return type(v)((x_new, y_new, z))

# --- END
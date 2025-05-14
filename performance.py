# performance.py
import time 

def tic():
    """
    Start a high-resolution timer.

    Returns:
        float: The current value of a high-precision performance counter,
               suitable for measuring short durations with `toc()`.

    Example:
        >>> t0 = tic()
        >>> # ... code to profile ...
        >>> toc(t0, "Section A")
    """
    return time.perf_counter()

def toc(initial, message = "", t_bound = 0.25):
    """
    Measure and optionally print the elapsed time since `initial`.

    Args:
        initial (float): Start time, typically obtained from `tic()`.
        message (str, optional): Message to prepend in the output. Defaults to "".
        t_bound (float, optional): Minimum duration in seconds required to print output.
                                   Prevents logging trivial timings. Defaults to 0.1.

    Returns:
        None

    Example:
        >>> t0 = tic()
        >>> heavy_computation()
        >>> toc(t0, "Computation done")  # prints if elapsed time > 0.1s

    Output (example):
        Computation done dt = 0.347
    """
    dt = time.perf_counter() - initial
    if dt < t_bound: return dt, f"{message}"
    print(f"{message} dt = {dt:.3f}")
    return dt, f"{message}" 


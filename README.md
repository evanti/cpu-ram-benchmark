# cpu-ram-benchmark
Measures cpu performance with heavy usage of RAM

Run this python script with the following parameters:

Number threads – plan it according to the cores available on the server and percentage of utilization that you're planning to achieve. If you request more threads than CPUs available to the OS, the script will break
Duration – total duration of the test in seconds.
Start delay – time in seconds between starting each new thread. Can be used to create ramp-up load. '0' means all threads start simultaneously. This parameter does not influence the duration, so if you start with 16 threads, 10 seconds duration and 1 second start delay, only 10 threads will be started within these 10 seconds.

The script will first compile C code into a binary, then run it with arguments provided. GCC must be available in the server.

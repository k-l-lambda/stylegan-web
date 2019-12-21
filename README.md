## Requirements

### For Windows

* MSVC

NOTE: Visual Studio 2019 is not compatible with CUDA 10.0.

* NVCC

test command:

```.bash
nvcc test_nvcc.cu -o test_nvcc -run -ccbin "C:\Program Files (x86\Microsoft VisualStudio\2017\BuildTools\VC\Tools\MSVC\14.16.27023\bin\Hostx64\x64"
```

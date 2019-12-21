## Requirements

### Python

Install requirement libraries with pip, reference to [requirements.txt](./requirements.txt).

### For Windows

* MSVC

	**NOTE**: Visual Studio 2019 is not compatible with CUDA 10.0.

	Append the actual msvc binary directory in *dnnlib/tflib/custom_ops.py*, the array of *compiler_bindir_search_path*. For example:

	```patch
	-	'C:/Program Files (x86)/Microsoft Visual Studio 14.0/vc/bin',
	+	'C:/Program Files (x86)/Microsoft Visual Studio/2017/BuildTools/VC/Tools/MSVC/14.16.27023/bin/Hostx64/x64',
	```

* NVCC

	test command:

	```.bash
	nvcc test_nvcc.cu -o test_nvcc -run -ccbin "C:\Program Files (x86)\Microsoft VisualStudio\2017\BuildTools\VC\Tools\MSVC\14.16.27023\bin\Hostx64\x64"
	```

* Tips for tensorflow 1.15

	*NVCC* compiling may encounter C++ including path issue. Solution: make a symbolic link in python installation fold `Python36\Lib\site-packages\tensorflow_core`:

	```.bash
	mklink /J tensorflow tensorflow_core
	```

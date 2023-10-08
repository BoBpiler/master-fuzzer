import ctypes


def make_cstring(py_str:str) :
    return ctypes.c_char_p(py_str.encode('utf-8'))



# Load the shared library
compilers_manager = ctypes.CDLL('./build/libcompile_manager.so')

# Define the function prototype
#lib.print_compilers.argtypes = (ctypes.POINTER(ctypes.POINTER(ctypes.c_char_p)), ctypes.c_int)
compilers_manager.py_compile.restype = ctypes.c_char_p
compilers_manager.py_exit_compilers.restype = ctypes.c_char_p


# Call the C function
ret = compilers_manager.py_init_compilers()
print(ret)

# Python string
py_string = "/home/dong/Downloads/fork_test/profileing/BoBpiler-fuzzer/compile_manager/uuid0/hello0.c\n"

# Convert to ctypes char*
c_string = make_cstring(py_string)


ret = compilers_manager.py_compile(c_string).decode('utf-8')
print(ret)

py_string = "/home/dong/Downloads/fork_test/profileing/BoBpiler-fuzzer/compile_manager/uuid1/hello1.c\n"
# Convert to ctypes char*
c_string = ctypes.c_char_p(py_string.encode('utf-8'))
ret = compilers_manager.py_compile(c_string).decode('utf-8')
print(ret)

ret = compilers_manager.py_exit_compilers().decode('utf-8')
print(ret)
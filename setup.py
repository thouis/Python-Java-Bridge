'''javabridge - Wraps the Java Native Interface (JNI) using Cython.

This code originated as part of the CellProfiler project.  
Website: http://www.cellprofiler.org
Copyright (c) 2003-2009 Massachusetts Institute of Technology
Copyright (c) 2009-2011 Broad Institute
It is maintained by Thouis Jones <thouis.jones@curie.fr>
It is licensed under the GPL and BSD licenses.
'''

import os
import sys
import subprocess
import traceback
is_win = sys.platform.startswith("win")
is_win64 = (is_win and (os.environ["PROCESSOR_ARCHITECTURE"] == "AMD64"))
is_msvc = (is_win and sys.version_info[0] >= 2 and sys.version_info[1] >= 6)
is_mingw = (is_win and not is_msvc)


from distutils.core import setup,Extension
from distutils.sysconfig import get_config_var
from numpy import get_include
from numpy.distutils.misc_util import Configuration
from Cython.Distutils import build_ext


# from http://packages.python.org/an_example_pypi_project/setuptools.html
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

def configuration(parent_package='',top_path=None):
    from numpy.distutils.misc_util import Configuration

    dict = { "name" : "javabridge",
             "version" : "0.1",
             "keywords" : "java native interface jni",
             "long_description" : read('README.txt'),
             "url" : "https://github.com/thouis/Python-Java-Bridge",
             "description" : "python wrapper for the Java Native Interface",
             "maintainer" : "Thouis Jones",
             "maintainer_email" : "thouis.jones@curie.fr",
             "classifiers" : ["Development Status :: 3 - Alpha"],
             "cmdclass": {'build_ext' : build_ext},
             "ext_modules": [setup_java_bridge_extension()]
             }

    config = Configuration('javabridge', parent_package, top_path, **dict)

    def add_test_directories(arg, dirname, fnames):
        if dirname.split(os.path.sep)[-1] == 'tests':
            config.add_data_dir(dirname)

    # Add test directories
    from os.path import isdir, dirname, join, abspath
    rel_isdir = lambda d: isdir(join(curpath, d))

    curpath = join(dirname(__file__), './')
    subdirs = [join(d, 'tests') for d in os.listdir(curpath) if rel_isdir(d)]
    subdirs = [d for d in subdirs if rel_isdir(d)]
    for test_dir in subdirs:
        config.add_data_dir(test_dir)

    return config
    

def find_javahome():
    """Find JAVA_HOME if it doesn't exist"""
    if hasattr(sys, 'frozen') and is_win:
        #
        # The standard installation of CellProfiler for Windows comes with a JRE
        #
        path = os.path.split(os.path.abspath(sys.argv[0]))[0]
        path = os.path.join(path, "jre")
        for jvm_folder in ("client", "server"):
            jvm_path = os.path.join(path, "bin", jvm_folder, "jvm.dll")
            if os.path.exists(jvm_path):
                # Problem: have seen JAVA_HOME != jvm_path cause DLL load problems
                if os.environ.has_key("JAVA_HOME"):
                    del os.environ["JAVA_HOME"]
                return path
    
    if os.environ.has_key('JAVA_HOME'):
        return os.environ['JAVA_HOME']
    if sys.platform == 'darwin':
        return "Doesn't matter"
    if is_win:
        import _winreg
        java_key_path = 'SOFTWARE\\JavaSoft\\Java Runtime Environment'
        looking_for = java_key_path
        try:
            kjava = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, java_key_path)
            looking_for = java_key_path + "\\CurrentVersion"
            kjava_values = dict([_winreg.EnumValue(kjava, i)[:2]
                                 for i in range(_winreg.QueryInfoKey(kjava)[1])])
            current_version = kjava_values['CurrentVersion']
            looking_for = java_key_path + '\\' + current_version
            kjava_current = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE,
                                            looking_for)
            kjava_current_values = dict([_winreg.EnumValue(kjava_current, i)[:2]
                                         for i in range(_winreg.QueryInfoKey(kjava_current)[1])])
            return kjava_current_values['JavaHome']
        except:
            traceback.print_exc()
            sys.stderr.write("Failed to find registry entry: %s\n" %looking_for)
            return None

def find_jdk():
    """Find the JDK under Windows"""
    if sys.platform == 'darwin':
        return "Doesn't matter"
    if is_win:
        import _winreg
        jdk_key_path = 'SOFTWARE\\JavaSoft\\Java Development Kit'
        kjdk = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, jdk_key_path)
        kjdk_values = dict([_winreg.EnumValue(kjdk, i)[:2]
                             for i in range(_winreg.QueryInfoKey(kjdk)[1])])
        current_version = kjdk_values['CurrentVersion']
        kjdk_current = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE,
                                       jdk_key_path + '\\' + current_version)
        kjdk_current_values = dict([_winreg.EnumValue(kjdk_current, i)[:2]
                                    for i in range(_winreg.QueryInfoKey(kjdk_current)[1])])
        return kjdk_current_values['JavaHome']
    

def setup_java_bridge_extension():
    #
    # Find JAVA_HOME, possibly from Windows registry
    #
    java_home = find_javahome()
    jdk_home = find_jdk()
    print "Using jdk_home = %s"%jdk_home
    include_dirs = [get_include()]
    extra_link_args = None
    libraries = None
    library_dirs = None
    javabridge_sources = [ "javabridge/javabridge.pyx" ]
    if is_win:
        if jdk_home is not None:
            jdk_include = os.path.join(jdk_home, "include")
            jdk_include_plat = os.path.join(jdk_include, sys.platform)
            include_dirs += [jdk_include, jdk_include_plat]
        if is_mingw:
            #
            # Build libjvm from jvm.dll on Windows.
            # This assumes that we're using mingw32 for build
            #
            cmd = ["dlltool", "--dllname", 
                   os.path.join(jdk_home,"jre\\bin\\client\\jvm.dll"),
                   "--output-lib","libjvm.a",
                   "--input-def","jvm.def",
                   "--kill-at"]
            p = subprocess.Popen(cmd)
            p.communicate()
            library_dirs = [os.path.abspath(".")]
        else:
            #
            # Use the MSVC lib in the JDK
            #
            jdk_lib = os.path.join(jdk_home, "lib")
            library_dirs = [jdk_lib]
            javabridge_sources.append("javabridge/strtoull.c")
    
        libraries = ["jvm"]
    elif sys.platform == 'darwin':
        include_dirs += ['/System/Library/Frameworks/JavaVM.framework/Headers']
        extra_link_args = ['-framework', 'JavaVM']
    elif sys.platform.startswith('linux'):
        include_dirs += [os.path.join(java_home,'include'),
                         os.path.join(java_home,'include','linux')]
        library_dirs = [os.path.join(java_home,'jre','lib','amd64','server')]
        libraries = ["jvm"]

    java_bridge_extension = Extension("javabridge/javabridge",
                                      sources=javabridge_sources,
                                      libraries=libraries,
                                      library_dirs=library_dirs,
                                      include_dirs=include_dirs,
                                      extra_link_args=extra_link_args)
    return java_bridge_extension


if __name__ == "__main__":
    from numpy.distutils.core import setup
    setup(**configuration(top_path='').todict())


